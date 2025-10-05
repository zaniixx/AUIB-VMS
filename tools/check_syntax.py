import py_compile
import sys
import pkgutil
import importlib
import os

def compile_package(pkg_name):
    try:
        pkg = importlib.import_module(pkg_name)
    except Exception as e:
        print(f'Failed to import {pkg_name}: {e}')
        return 2
    pkg_path = os.path.dirname(pkg.__file__)
    rc = 0
    for root, dirs, files in os.walk(pkg_path):
        for f in files:
            if f.endswith('.py'):
                fp = os.path.join(root, f)
                try:
                    py_compile.compile(fp, doraise=True)
                    print(f'OK: {fp}')
                except py_compile.PyCompileError as e:
                    print(f'COMPILE ERROR: {fp}: {e}')
                    rc = 1
    return rc

if __name__ == '__main__':
    pkg = sys.argv[1] if len(sys.argv) > 1 else 'vms'
    rc = compile_package(pkg)
    sys.exit(rc)
