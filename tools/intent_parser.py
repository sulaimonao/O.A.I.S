def parse_intent(message):
    if "write to file" in message.lower() and "poem" in message.lower():
        return "write_poem"
    if "write/execute" in message.lower() and "analyze the following data sets" in message.lower():
        return "analyze_data"
    return "unknown"

def handle_write_poem(message):
    poem = "A poem about the ocean:\nVast and deep, the ocean blue,\nWaves that dance and skies so true.\nWhispers of the sea breeze call,\nMysteries beneath, they enthrall."
    from .file_operations import write_file
    write_file('poem.txt', poem)
    return poem

def handle_analyze_data(message):
    from .code_execution import execute_code
    data_analysis_code = """
import pandas as pd

# Example data
data = {
    'A': [1, 2, 3],
    'B': [4, 5, 6]
}
df = pd.DataFrame(data)
result = df.describe()
print(result)
"""
    result = execute_code(data_analysis_code)
    from .file_operations import write_file
    write_file('data_analysis_result.txt', result)
    return result
