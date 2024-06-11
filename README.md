# MongoDB Querying with LLM

This repository provides a tool for querying MongoDB databases using a Language Learning Model (LLM) integrated into a FastAPI framework. It's designed to facilitate easy interaction with your MongoDB data through a simple API.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python Version**: The codebase is tested with Python 3.11.9. Other versions might work but are not guaranteed. It is highly recommended to use Python 3.11.9 to avoid any compatibility issues.

## Installation

Follow these steps to get your development environment set up:

1. Clone the repository:
   ```bash
   git clone https://github.com/qolaba/QueryGen.git
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To start the application, run the following command in your terminal:

```bash
python main.py
```

After running the application, you can access the FastAPI documentation by navigating to `http://localhost:9000/docs` in your web browser. This documentation page will provide you with all the available endpoints and their respective details.

## FastAPI Endpoint

The FastAPI server provides an interactive API documentation (Swagger UI) that lets you test the API directly from your browser. You can access the API documentation by visiting the `/docs` endpoint after starting the server.

## API Endpoint Parameters

When interacting with the FastAPI endpoint, you are required to provide several parameters. Here's a detailed description of each:

- **connection_url**: The URL used to connect to your MongoDB instance. This should include the username, password, and the cluster address. Make sure that, your connection URL does not have editing access in associated database. 

- **collection_list**: An array of strings representing the names of the collections you want to query within the specified database. From the given collection list, the DBReader object will read the unique keys and associated unique examples and prepare the system prompt for that. If you are writing some query, make sure that collection list contains the collection associated with this query. Additionally, the DB reader will only add keys which are mostly repeating to avoid less repeating keys. Additionally, the examples values are only added if given keys are not object id or date to save tokens because the final system prompt will be too larger.

- **database_name**: The name of the database where the collections reside. 

- **description**: A detailed description of guidelines or notes relevant to constructing your queries or understanding the database schema. If you have specific logic for your given database, you could describe them here.

- **query**: A description or specific question you want the LLM to process and generate MongoDB queries for. This should be formulated in natural language. After generating query, it will execute the query through pymonog and return final answer.

- **example_count**: This parameter specify the number of unique examples added in system prompt for given key.

- **max_output_count**: This limits the number of query results returned. Example: `30`. The reason for specifying max_count is that, the model will generate query and it could results in 1000s or more data output from database. At the end, the fetched data will be passed to LLM for generating answer in human understandable way. During this time, if we add too large amount of data, LLM could not be able to answer this due to token limit. To avoid this scenario, we could fix this max_output_count. It will only fetch first max_output_count number of results. 

- **database_type**: The type of database being queried. Currently, this repo, only supports MongoDB.

- **llm_name**: The specific version or name of the Language Learning Model used for generating queries. Example: `"gpt-4-turbo-2024-04-09"`. Currently, this repo supports MistralAI codestral model and OpenAI GPT 4 model. 

- **temperature**: A parameter controlling the randomness of the output from the LLM. A temperature close to 0 makes the model's output more deterministic and repetitive, while higher values make it more diverse and random. Example: `0`.

Each of these parameters plays a crucial role in how the API functions and serves the user's requests. Ensure that these parameters are correctly specified to achieve the desired outcomes from your API.

## Workflow Description

The operation of this repository revolves around a structured process involving data preparation, query generation, and result processing using a Language Learning Model (LLM). Here is a detailed breakdown of the workflow:

1. **Data Preparation with DBReader**:
   - The `DBReader` object initializes by fetching all unique keys, their associated values, and data types from the collections specified in the `collection_list`.
   - It then arranges this data into a structured prompt, listing all keys associated with each collection, along with maximum example values and data types. This organization is performed for every collection in the list.

2. **Query Generation by LLM**:
   - The prepared data, along with the user's query, is passed to the LLM.
   - The LLM processes this information to generate a MongoDB query and specifies the collection on which this query should be executed.

3. **Condition Checking**:
   - The system checks the generated query against four conditions:
     - **Intermediate Query Check**: Determines if the query is an intermediate step, i.e., if it cannot fetch all required data in a single step for the user's query.
     - **Operation Check**: Identifies if the query includes delete, modify, or insert operations.
     - **Syntax Check**: Validates the syntactical correctness of the query.
     - **Raw Result Check**: Ensures the query does not return raw results, like object IDs, directly to the user.
   - If any condition is true, the LLM is prompted to rewrite the query, providing reasons based on the condition that failed.

4. **Data Fetching**:
   - Once all the condiitons are satisfied, The generated query is executed through a designated function that fetches the required data from the database.


5. **Result Fetching and Error Handling**:
   - If an error occurs during above step, the LLM is asked to rewrite the query to rectify the error by passing the old query and the error message back to the LLM.

6. **Final Response Crafting**:
   - Once the query successfully runs without errors, the output is passed back to the LLM, which then crafts the final response in a human-understandable format.

7. **Iteration and Termination**:
   - The process includes a maximum iteration condition to prevent infinite loops. If the number of iterations exceeds the `max_iteration` limit, the process is stopped.

This workflow ensures a robust interaction between the MongoDB database and the LLM, facilitating accurate and secure data handling and query generation.


## Setting Up Environment Variables

To ensure the effective operation of the Language Learning Models (LLMs) and the associated API, it is essential to configure several environment variables. These variables facilitate authentication with external services and simplify the configuration of the application. Below are the steps and details for setting up these environment variables:

### Required Environment Variables

- **MISTRALAI_API_KEY**: Needed to authenticate with MistralAI services.
- **OPENAI_API_KEY**: Required for authentication with OpenAI services.
- **API_KEY**: Used to authenticate API requests within your FastAPI application.

### Optional Environment Variables

In addition to the essential keys for API authentication, you can also set the following parameters as environment variables to streamline your workflow and avoid the need to specify these parameters manually each time you run the application:

- **CONNECTION_URL**: The MongoDB connection URL.
- **COLLECTION_LIST**: A list of database collections to be queried.
- **DATABASE_NAME**: The name of the MongoDB database.
- **QUERY**: A default query to run when testing or developing.

### Configuring Environment Variables

You can set these environment variables through your operating system's environment settings. Alternatively, for ease of development, you can use a `.env` file placed in the root directory of your project. This file can be loaded using libraries like `dotenv` in Python, which simplifies the management of configuration settings.
