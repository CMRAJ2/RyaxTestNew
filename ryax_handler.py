import pyodbc
import openai
import pandas as pd
import logging


def handle(ryax_input):
    openai.api_type = ryax_input["openai_type"]
    openai.api_base = ryax_input["openai_base"]
    openai.api_version = ryax_input["openai_version"]
    openai.api_key = ryax_input["openai_key"]

    server = ryax_input["mssql_server"]
    username = ryax_input["mssql_username"]
    password = ryax_input["mssql_password"]
    database = ryax_input["mssql_database"]

    # Create a connection sql string
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

    # Establish a connection
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    col_query = 'SELECT DISTINCT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS'
    cursor.execute(col_query)

    # Fetch all the column names
    columns = [row.COLUMN_NAME for row in cursor.fetchall()]
    logging.info(f'{columns}')
    tab_query ='SELECT DISTINCT TABLE_NAME FROM INFORMATION_SCHEMA.COLUMNS'
    cursor.execute(tab_query)
    tables = [row.TABLE_NAME for row in cursor.fetchall()]
    logging.info(f'{tables}')
    prompt_description = "\n### MSSql with the data\n\n\ncolumns:{columns}\n\n\ntables:{tables}\n"

    # Get input from the user now
    user_question = ryax_input["user_query"]
    prompt_user_input = f'### A query to answer: {user_question} \n SELECT'

    # Final prompt to send to OpenAI
    final_prompt = prompt_description + prompt_user_input

    response = openai.Completion.create(
         engine="gpt-35-turbo",
         prompt=final_prompt,
         temperature=0,
         max_tokens=150,
         top_p=1.0,
         frequency_penalty=0,
         presence_penalty=0,
         stop=["#", ";"])

    query = "SELECT" + response["choices"][0]["text"]
    logging.info(f'{query}')
    cursor.execute(query)
    result = [str(row) for row in cursor.fetchall()]
    result_df = pd.DataFrame(result)
    result_file = '/tmp/result.csv'
    result_df.to_csv(result_file)

    print({ "query_result_file": result_file })



# This is used only for local tests as a standalone script, it is ignored by ryax
# To test it feed the correct parameters and run with:
# python3 ryax_handler.py
if __name__ == "__main__":
    handle({
        "openai_type": "azure",
        "openai_base": "https://insigence-azureopenai-dev-01.openai.azure.com/",
        "openai_version": "2022-12-01",
        "openai_key": "58c84038d46d4b44afc0906f77b04668",
        "mssql_server": "sql-server-cmraj.database.windows.net",
        "mssql_username": "sqlserver-admin-cmraj",
        "mssql_password": "Sunny@305",
        "mssql_database": "sql-db-cmraj",
        "user_query": "i want average value of city id from soccer city table",
    })
