import os

import oneiot_core.env as env
import oneiot_core.Parsers as Parsers

def set_variable(variable, value):
    # Set globally
    env = Parsers.EnvParser("/etc/environment")
    env.vars[variable] = value
    env.save()
    # Update in this session
    os.system(f'export {variable}="{value}"')

def unset_variable(variable):
    # Set globally
    env = Parsers.EnvParser("/etc/environment")
    if variable in env.vars:
        del env.vars[variable]
    env.save()
    # Update in this session
    os.system(f'unset {variable}')
