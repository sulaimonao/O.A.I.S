import os
import glob
import json
from pathlib import Path
from datetime import datetime

def crawl_repository(base_dir):
    project_structure = {}

    # Define the file extensions you're interested in
    extensions = {
        'python': '*.py',
        'html': '*.html',
        'javascript': '*.js',
        'css': '*.css',
        # Add other essential file types if needed
    }

    # Directories to exclude from scanning
    excluded_dirs = {'venv', 'env', '.env', '__pycache__', 'node_modules', '.git', '.idea', '.vscode', 'shared_venv'}

    # Function to check if a file is in an excluded directory
    def is_excluded(path):
        for excluded_dir in excluded_dirs:
            if excluded_dir in Path(path).parts:
                return True
        return False

    # Traverse the directory and categorize files
    for category, pattern in extensions.items():
        project_structure[category] = []
        # Use os.walk to traverse directories while respecting excluded directories
        for dirpath, dirnames, filenames in os.walk(base_dir):
            # Modify dirnames in-place to skip excluded directories
            dirnames[:] = [d for d in dirnames if d not in excluded_dirs]
            for filename in filenames:
                if is_excluded(os.path.join(dirpath, filename)):
                    continue
                if glob.fnmatch.fnmatch(filename, pattern):
                    filepath = os.path.join(dirpath, filename)
                    file_info = {
                        'name': filename,
                        'path': os.path.relpath(filepath, base_dir),
                        'size': os.path.getsize(filepath),
                        'last_modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                    }
                    project_structure[category].append(file_info)
    
    # Add directory tree structure (excluding environment directories)
    project_structure['directories'] = []
    for dirpath, dirnames, filenames in os.walk(base_dir):
        dirnames[:] = [d for d in dirnames if d not in excluded_dirs]
        if is_excluded(dirpath):
            continue
        project_structure['directories'].append({
            'directory': os.path.relpath(dirpath, base_dir),
            'subdirectories': dirnames,
            'files': filenames
        })

    # Summarize and write the report
    report_file = os.path.join(base_dir, 'project_overview.json')
    with open(report_file, 'w') as report:
        json.dump(project_structure, report, indent=4)
    
    return project_structure, report_file

if __name__ == "__main__":
    # Replace this with the root directory of your repo
    repo_path = str(Path(__file__).parent)
    project_overview, report_path = crawl_repository(repo_path)
    
    # Output the report file location
    print(f"Project overview report saved at: {report_path}")
    print("Here’s a summary of the structure:")
    
    # Print out a summary of the project structure
    for category, files in project_overview.items():
        if category == 'directories':
            continue  # Skip printing directory details here
        print(f"\nCategory: {category}")
        for file_info in files:
            print(f"  - {file_info['name']} ({file_info['size']} bytes) last modified: {file_info['last_modified']} in {file_info['path']}")
    
    # Optionally, print the directory tree structure
    # Uncomment the following lines if you wish to see the directory structure
    # print("\nDirectory Structure:")
    # for dir_info in project_overview['directories']:
    #     print(f"Directory: {dir_info['directory']}")
    #     print(f"  Subdirectories: {', '.join(dir_info['subdirectories'])}")
    #     print(f"  Files: {', '.join(dir_info['files'])}")
