import os
import sys
import subprocess
import webbrowser

def generate_docs():
    """
    Generates HTML documentation for the project using pdoc.
    """
    print("Generating documentation...")
    
    # Ensure the output directory exists
    output_dir = os.path.join("docs", "html")
    os.makedirs(output_dir, exist_ok=True)
    
    # The list of modules to document
    modules = ["game", "main"]
    
    # Construct the pdoc command
    # -o: Output directory
    # --math: Enable mathjax for mathematical formulas in docs
    cmd = ["pdoc", "-o", output_dir, "--math"] + modules
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Documentation generated successfully in {output_dir}")
        
        index_path = os.path.join(output_dir, "index.html")
        print(f"Open the following file in your browser to view:")
        print(f"file://{os.path.abspath(index_path)}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error generating documentation: {e}")
    except FileNotFoundError:
        print("Error: 'pdoc' is not installed. Please run: pip install pdoc")

if __name__ == "__main__":
    # Add the project root to python path so pdoc can find the modules
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    generate_docs()
