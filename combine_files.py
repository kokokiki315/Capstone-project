import os

# File extensions to include in the combined output
EXTENSIONS = {'.py', '.yaml', '.json', '.txt', '.md', '.jsx', '.ts', '.tsx', '.html', '.css', '.js','.cpp'}

# Directories to strictly ignore
IGNORE_DIRS = {
    '__pycache__', 
    '.git', 
    '.idea', 
    '.vscode',
    'env', 
    'node_modules',
    'dist',
    'build',
    'models',
    'test',
    'tests',
    'app',
    'data',
    'analyses',
    'thumbnails','combined_dataset','Frames',
    'runs'
}

# Specific filenames to ignore (optional)
IGNORE_FILES = {
    'package-lock.json',
    '.DS_Store'
    ,'datasets.txt','env'
}

def combine_files(output_file='_full_project_context.txt'):
    """
    Walks through the current directory and combines code files into a single text file.
    """
    # Get the name of this script so we don't include it in the output
    this_script_name = os.path.basename(__file__)
    
    count = 0
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        # Walk through all directories starting from current (.)
        for root, dirs, files in os.walk("."):
            # Modify dirs in-place to skip ignored directories
            # We use a list copy [:] to allow safe modification during iteration
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                # Skip specific ignored files
                if file in IGNORE_FILES:
                    continue
                    
                file_ext = os.path.splitext(file)[1]
                
                # Check if file has valid extension and is not this script or the output file
                if (file_ext in EXTENSIONS and 
                    file != this_script_name and 
                    file != output_file):
                    
                    file_path = os.path.join(root, file)
                    
                    # distinct separator so the AI knows where files start/end
                    outfile.write(f"\n{'='*40}\n")
                    outfile.write(f"FILE START: {file_path}\n")
                    outfile.write(f"{'='*40}\n")
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read())
                            count += 1
                            print(f"Added: {file_path}")
                    except Exception as e:
                        outfile.write(f"\n# Error reading file: {e}\n")
                        print(f"Error reading {file_path}: {e}")
                        
                    outfile.write(f"\n\nFILE END: {file_path}\n")

    print(f"\nDone! Combined {count} files into '{output_file}'.")

if __name__ == "__main__":
    combine_files()