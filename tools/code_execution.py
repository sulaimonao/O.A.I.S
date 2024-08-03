import execnet

def execute_code(code):
    gw = execnet.makegateway()
    channel = gw.remote_exec("""
        def execute_remote(code):
            exec(code, {'__builtins__': {}})
            return "Code executed successfully"

        channel.send(execute_remote(channel.receive()))
    """)
    channel.send(code)
    return channel.receive()
