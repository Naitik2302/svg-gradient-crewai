import os
import re
import json
from openai import OpenAI
from openai import AuthenticationError, RateLimitError
from crewai import Agent, Task, Crew
from crewai.process import Process

# -----------------------------
# Configuration
# -----------------------------
# Get API key from environment variable or use placeholder
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_api_key_here")

# Enable LLM only if we have a valid API key
ENABLE_LLM = OPENAI_API_KEY != "your_api_key_here"

if ENABLE_LLM:
    client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ LLM enabled with OpenAI API")
else:
    client = None
    print("⚠️  LLM disabled - using regex parser only")

# Load input SVG (for demo, hardcoded)
INPUT_SVG = """<svg width="300" height="300" xmlns="http://www.w3.org/2000/svg">
  <rect id="hero" x="50" y="50" width="200" height="100" fill="red"/>
  <circle cx="150" cy="200" r="40" fill="green"/>
  <rect x="20" y="20" width="50" height="50" fill="blue" class="small-box"/>
</svg>"""

# Enhanced color mapping with more colors and case insensitivity
COLOR_MAP = {
    'red': '#ff0000', 'green': '#00ff00', 'blue': '#0000ff', 
    'white': '#ffffff', 'black': '#000000', 'yellow': '#ffff00', 
    'purple': '#800080', 'orange': '#ffa500', 'gray': '#808080', 
    'grey': '#808080', 'cyan': '#00ffff', 'magenta': '#ff00ff', 
    'lime': '#00ff00', 'maroon': '#800000', 'navy': '#000080', 
    'olive': '#808000', 'teal': '#008080', 'silver': '#c0c0c0',
    'gold': '#ffd700', 'pink': '#ffc0cb', 'brown': '#a52a2a'
}

# Case-insensitive color lookup
def get_hex_color(color_str):
    color_lower = color_str.lower()
    return COLOR_MAP.get(color_lower, color_str)

# -----------------------------
# Gradient Parser Agent
# -----------------------------
class GradientParserAgent:
    def __init__(self):
        self.agent = Agent(
            role='Gradient Parser Specialist',
            goal='Transform natural language instructions about SVG gradients into structured JSON configurations',
            backstory="""With extensive experience in interpreting design instructions, you excel at 
            identifying target elements by ID, class, or tag type. You precisely determine gradient 
            characteristics including type (linear or radial), directionality, and color specifications 
            whether expressed as hex codes or common color names.""",
            verbose=True,
            allow_delegation=False
        )
    
    def parse_instruction(self, instruction: str):
        """
        Convert natural language gradient instructions into structured configurations.
        Uses advanced language models when available, with regex fallback when needed.
        """
        if ENABLE_LLM and client:
            try:
                print("🔍 Using advanced language processing for instruction analysis...")
                resp = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": """You specialize in converting gradient instructions to structured JSON format:
                        {
                            "steps": [
                                {
                                    "targets": [{"selector": "css_selector", "description": "element description"}],
                                    "gradient": {
                                        "type": "linear|radial",
                                        "direction": "horizontal|vertical|diagonal",
                                        "stops": [
                                            {"offset": 0, "color": "#color1"},
                                            {"offset": 100, "color": "#color2"}
                                        ]
                                    }
                                }
                            ]
                        }"""},
                        {"role": "user", "content": instruction}
                    ]
                )
                parsed = resp.choices[0].message.content.strip()
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', parsed, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    print("✅ Instruction successfully parsed using advanced processing")
                    return data
            except ImportError:
                print("⚠️  Advanced processing package not available, using standard parser")
            except AuthenticationError:
                print("⚠️  Authentication issue, using standard parser")
            except RateLimitError:
                print("⚠️  Processing limit reached, using standard parser")
            except Exception as e:
                print(f"⚠️  Advanced processing unavailable ({type(e).__name__}: {e}), using standard parser")

        # -----------------------------
        # Standard parser (reliable fallback)
        # -----------------------------
        print("🔍 Using standard text parser for instruction analysis...")
        
        # Enhanced target identification
        def identify_target(command_text):
            # Check for ID references
            id_match = re.search(r'id\s*[`\'"]?(\w+)[`\'"]?', command_text, re.I)
            if id_match:
                return f"#{id_match.group(1)}", f"element with id '{id_match.group(1)}'"
            
            # Check for class references
            class_match = re.search(r'class\s*[`\'"]?([\w-]+)[`\'"]?', command_text, re.I)
            if class_match:
                return f".{class_match.group(1)}", f"element with class '{class_match.group(1)}'"
            
            # Check for shape references
            if re.search(r'\ball circles?\b', command_text, re.I):
                return "circle", "all circles"
            elif re.search(r'\ball rectangles?\b', command_text, re.I):
                return "rect", "all rectangles"
            elif re.search(r'\bcircle\b', command_text, re.I):
                return "circle", "circle"
            elif re.search(r'\b(?:rect|rectangle)\b', command_text, re.I):
                return "rect", "rectangle"
            
            return None, "element"
        
        # Split compound instructions into individual commands
        commands = re.split(r"\s*(?:,|and|then)\s+", instruction, flags=re.I)
        gradient_configurations = []
        
        for cmd in commands:
            cmd = cmd.strip()
            if not cmd:
                continue
                
            print(f"  Processing command: '{cmd}'")
            
            # Identify target element
            target, target_description = identify_target(cmd)
            
            # Determine gradient style
            gradient_type = "linear"
            if "radial" in cmd.lower():
                gradient_type = "radial"
            
            # Determine gradient orientation
            direction = "horizontal"
            if "vertical" in cmd.lower():
                direction = "vertical"
            elif "diagonal" in cmd.lower():
                direction = "diagonal"
            
            # Extract color information
            color_pattern = r'(#(?:[0-9a-fA-F]{3,6})|\b(?:red|green|blue|white|black|yellow|purple|orange|gray|grey|cyan|magenta|lime|maroon|navy|olive|teal|silver|gold|pink|brown)\b)'
            color_matches = re.findall(color_pattern, cmd, re.I)
            
            # Convert color names to standardized hex codes
            hex_colors = []
            for color_value in color_matches:
                hex_colors.append(get_hex_color(color_value))
            
            # Provide default colors if insufficient specifications
            if len(hex_colors) < 2:
                hex_colors = ['#ff0000', '#0000ff']  # Default red to blue
            
            gradient_configurations.append({
                "targets": [{"selector": target if target else "rect", "description": target_description}],
                "gradient": {
                    "type": gradient_type,
                    "direction": direction,
                    "stops": [
                        {"offset": 0, "color": hex_colors[0]},
                        {"offset": 100, "color": hex_colors[1]}
                    ]
                }
            })

        result = {"steps": gradient_configurations}
        print("✅ Parsing completed:", json.dumps(result, indent=2))
        return result

# -----------------------------
# SVG Modifier Agent
# -----------------------------
class SVGModifierAgent:
    def __init__(self):
        self.agent = Agent(
            role='SVG Modification Expert',
            goal='Apply gradient definitions to SVG elements based on configuration specifications',
            backstory="""As a specialist in SVG document manipulation, you expertly handle gradient 
            applications and element modifications. Your precision ensures accurate implementation 
            of design specifications while maintaining document integrity.""",
            verbose=True,
            allow_delegation=False
        )
    
    def apply_gradients(self, svg_content: str, configuration: dict):
        print("🎨 Implementing gradient modifications to SVG document")
        
        gradient_definitions = []
        gradient_counter = 1
        
        for step in configuration["steps"]:
            gradient_id = f"grad{gradient_counter}"
            gradient_info = step["gradient"]
            
            print(f"  Creating {gradient_info['type']} gradient {gradient_id} for targets: {[t['selector'] for t in step['targets']]}")

            # Create appropriate gradient definition
            if gradient_info["type"] == "linear":
                if gradient_info["direction"] == "vertical":
                    gradient_def = f'<linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="0%" y2="100%">'
                elif gradient_info["direction"] == "diagonal":
                    gradient_def = f'<linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="100%" y2="100%">'
                else:  # horizontal default
                    gradient_def = f'<linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="100%" y2="0%">'
            else:  # radial gradient
                gradient_def = f'<radialGradient id="{gradient_id}" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">'

            # Add color transition points
            for stop_point in gradient_info["stops"]:
                color_value = stop_point["color"]
                # Standardize color format
                if not color_value.startswith('#') and color_value.lower() in COLOR_MAP:
                    color_value = COLOR_MAP[color_value.lower()]
                gradient_def += f'<stop offset="{stop_point["offset"]}%" style="stop-color:{color_value};stop-opacity:1" />'
            
            gradient_def += '</linearGradient>' if gradient_info["type"] == "linear" else '</radialGradient>'
            gradient_definitions.append(gradient_def)

            # Apply gradient to specified elements
            for target_element in step["targets"]:
                selector = target_element["selector"]
                print(f"    Applying gradient to: {selector}")
                
                if selector.startswith("#"):  # ID-based selection
                    element_id = selector[1:]
                    pattern = f'<([^>]*id="{re.escape(element_id)}"[^>]*)fill="[^"]*"'
                    replacement = f'<\\1fill="url(#{gradient_id})"'
                    svg_content = re.sub(pattern, replacement, svg_content)
                    
                elif selector.startswith("."):  # Class-based selection
                    class_name = selector[1:]
                    pattern = f'<([^>]*class="[^"]*{re.escape(class_name)}[^"]*"[^>]*)fill="[^"]*"'
                    replacement = f'<\\1fill="url(#{gradient_id})"'
                    svg_content = re.sub(pattern, replacement, svg_content)
                    
                else:  # Tag-based selection
                    pattern = f'<({re.escape(selector)}[^>]*)fill="[^"]*"'
                    replacement = f'<\\1fill="url(#{gradient_id})"'
                    svg_content = re.sub(pattern, replacement, svg_content)

            gradient_counter += 1

        # Insert gradient definitions with proper placement
        definitions_block = "<defs>" + "".join(gradient_definitions) + "</defs>"
        if "<defs>" in svg_content:
            # Replace existing definitions
            svg_content = re.sub(r'<defs>.*?</defs>', definitions_block, svg_content, flags=re.DOTALL)
        else:
            # Insert definitions after opening SVG tag
            svg_content = re.sub(r'(<svg[^>]*>)', r'\1' + definitions_block, svg_content, 1)
        
        return svg_content

# -----------------------------
# Integrity Checker Agent
# -----------------------------
class IntegrityCheckerAgent:
    def __init__(self):
        self.agent = Agent(
            role='Quality Assurance Validator',
            goal='Ensure SVG output maintains structural integrity and functional correctness',
            backstory="""With meticulous attention to detail, you specialize in validating SVG documents 
            for proper structure, reference consistency, and rendering compatibility. Your expertise 
            ensures final outputs meet professional standards.""",
            verbose=True,
            allow_delegation=False
        )
    
    def validate_svg(self, svg_content: str):
        print("🔍 Conducting comprehensive SVG validation")
        
        validation_issues = []
        
        # Verify proper SVG structure
        if not re.match(r'^\s*<svg[^>]*>', svg_content):
            validation_issues.append("Document missing valid SVG root element")
        
        # Check definition section integrity
        if "<defs>" in svg_content:
            defs_start = svg_content.find("<defs>")
            defs_end = svg_content.find("</defs>")
            if defs_end <= defs_start:
                validation_issues.append("Definition section improperly structured")
            elif defs_start < svg_content.find(">", svg_content.find("<svg")):
                validation_issues.append("Definition section must follow opening SVG tag")
        
        # Verify gradient reference consistency
        gradient_references = re.findall(r'url\(#([^)]+)\)', svg_content)
        gradient_definitions = re.findall(r'<[^>]*id="([^"]+)"', svg_content)
        
        for reference in gradient_references:
            if reference not in gradient_definitions:
                validation_issues.append(f"Gradient reference '{reference}' lacks corresponding definition")
        
        return {"valid": len(validation_issues) == 0, "errors": validation_issues}

# -----------------------------
# CrewAI Setup and Execution
# -----------------------------
def create_svg_gradient_crew():
    """Establish and configure the SVG Gradient processing team"""
    
    # Initialize specialized team members
    parser_agent = GradientParserAgent()
    modifier_agent = SVGModifierAgent()
    checker_agent = IntegrityCheckerAgent()
    
    # Define processing tasks
    parsing_task = Task(
        description="Analyze and interpret natural language gradient instructions",
        agent=parser_agent.agent,
        expected_output="Structured JSON configuration detailing gradient specifications"
    )
    
    modification_task = Task(
        description="Implement gradient configurations within SVG document",
        agent=modifier_agent.agent,
        expected_output="Modified SVG document with applied gradient definitions",
        context=[parsing_task]
    )
    
    validation_task = Task(
        description="Verify structural and functional integrity of modified SVG",
        agent=checker_agent.agent,
        expected_output="Comprehensive validation report with issue identification",
        context=[modification_task]
    )
    
    # Assemble processing team
    processing_crew = Crew(
        agents=[parser_agent.agent, modifier_agent.agent, checker_agent.agent],
        tasks=[parsing_task, modification_task, validation_task],
        verbose=True,
        process=Process.sequential
    )
    
    return processing_crew, parser_agent, modifier_agent, checker_agent

# -----------------------------
# Main program
# -----------------------------
def main():
    print("=" * 60)
    print("          SVG Gradient Processing System")
    print("=" * 60)
    
    print("\n--- INPUT SVG ---")
    print(INPUT_SVG)
    
    instruction = input("\nEnter your gradient instruction: ")
    if not instruction:
        instruction = "Apply a diagonal gradient from #123456 to #abcdef to all circles and give the element with id 'hero' a radial gradient from red to white"
        print(f"Using example instruction: {instruction}")
    
    print("\n--- PROCESSING LOG ---")
    
    # Establish processing team
    crew, parser_agent, modifier_agent, checker_agent = create_svg_gradient_crew()
    
    # Execute processing workflow
    # 1. Instruction analysis
    print("\n1. Instruction Analysis Phase:")
    configuration = parser_agent.parse_instruction(instruction)
    
    # 2. SVG modification
    print("\n2. SVG Modification Phase:")
    modified_svg = modifier_agent.apply_gradients(INPUT_SVG, configuration)
    
    # 3. Quality validation
    print("\n3. Quality Validation Phase:")
    validation_results = checker_agent.validate_svg(modified_svg)
    
    if validation_results["valid"]:
        print("   ✅ Validation successful!")
    else:
        print("   ❌ Validation identified issues:")
        for issue in validation_results["errors"]:
            print(f"      - {issue}")
    
    print("\n--- FINAL OUTPUT ---")
    print(modified_svg)
    
    # Save results to file
    with open("output.svg", "w", encoding="utf-8") as f:
        f.write(modified_svg)
    print("\n✅ Results saved to output.svg")
    
    print("\n--- PROCESSING SUMMARY ---")
    print(f"Original elements: 3 (red rectangle, green circle, blue rectangle)")
    print(f"Gradient applications: {len(configuration['steps'])}")
    print(f"Quality assurance: {'PASS' if validation_results['valid'] else 'FAIL'}")
    
    # Team performance summary
    print("\n--- TEAM PERFORMANCE SUMMARY ---")
    print("✅ Instruction Analysis: Completed successfully")
    print("✅ SVG Modification: Completed successfully") 
    print("✅ Quality Validation: Completed successfully")
    print("🎉 Processing workflow completed!")


if __name__ == "__main__":
    main()