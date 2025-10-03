import os

def create_structure():
    """Create directory structure"""
    dirs = [
        "middleware",
        "models", 
        "routers",
        "database",
        "scripts"
    ]
    
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        init_file = os.path.join(dir_name, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write(f"# {dir_name} module\n")
    
    print("✅ Directory structure created")

if __name__ == "__main__":
    create_structure()
