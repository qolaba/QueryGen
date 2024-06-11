import pymongo
import pymongo.collection
from textwrap import dedent

class BaseDBReader:
    def __init__(self) -> None:
        pass

    def get_collection(self):
        pass

    def run_pipeline_query(self):
        pass
    
    def get_distinct_keys(self):
        pass

    def prepare_collection_schema_json(self):
        pass

    def prepare_schema_prompt(self):
        pass


class MongoReader(BaseDBReader):
    def __init__(self, connection_url : str, database_name : str) -> None:
        self.client = pymongo.MongoClient(connection_url)
        self.database = self.client[database_name]

    def get_collection(self, collection_name : str) -> pymongo.collection.Collection:
        return self.database[collection_name]
    
    def run_pipeline_query(self, collection_name : str, pipeline_query : list[dict], fetch_result : bool = False) -> list[dict]:
        collection = self.get_collection(collection_name)
        result = collection.aggregate(pipeline_query)

        if fetch_result:
            output = []
            for i in result:
                output.append(i)
            return output

        return result
    
    def get_distinct_keys(self, collection_name : str, key : str, key_count : int) -> list[str]:
        collection = self.get_collection(collection_name)
        pipeline = [
            {'$group': {'_id': f'${key}'}},  # Group by the 'category' field
            {'$limit': key_count}             # Limit the number of results
        ]
        return collection.aggregate(pipeline)

    def prepare_collection_schema_json(self, collection_list : list[str], max_key_example_count : int) -> dict[str, dict]:

        pipeline = [
            {"$project": {"arrayofkeyvalue": {"$objectToArray": "$$ROOT"}}},
            {"$unwind": "$arrayofkeyvalue"},
            {"$group": {"_id": "$arrayofkeyvalue.k", "count": {"$sum": 1}, "types": {"$addToSet": {"$type": "$arrayofkeyvalue.v"}}}}
        ]

        collection_key_list : dict[str, dict] = {}

        for collection_name in collection_list:
            result = self.run_pipeline_query(collection_name, pipeline) 
            output = []
            max_key_count = 0
            for doc in result:
                output.append(doc)
                if(doc["count"] > max_key_count):
                    max_key_count = doc["count"]

            key_types = {}
            for doc in output:
                if(doc["count"] > max_key_count/2):
                    key_types[doc['_id']] =  doc['types']

            collection_key_list[collection_name] = key_types


        for collection_name, key_data in collection_key_list.items():
            for key, types in key_data.items():

                key_count = max_key_example_count
                if(types[0] in ["date", "objectId"]):
                    key_count = 1
                result = list(self.get_distinct_keys(collection_name, key, key_count))
                

                collection_key_list[collection_name][key] = {
                    "data_type" : types,
                    "Example_values" : [str(result[i]["_id"])[0 : 100] for i in range(0, len(result))]
                }

        return collection_key_list
    
    def prepare_schema_prompt(self, collection_list : list[str], max_key_example_count : int) -> str:
        collection_data = self.prepare_collection_schema_json(collection_list, max_key_example_count)
        output_string = []
        for collection, schema in collection_data.items():
            output_string.append(dedent(
                f"""
                =============================================================
                Name of Collection : {collection} 
                =============================XX==============================
                Output Schema Associated with {collection}:"""
            ))

            for key, data_dict in schema.items():

                output_string.append(dedent(
                    f"""
                    "{key}" -> data_type : {data_dict["data_type"][0]}, 
                    Example_Values : {" || ".join(data_dict["Example_values"])}
                    """))
                
        return "\n".join(output_string)
