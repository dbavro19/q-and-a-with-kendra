import streamlit as st
import boto3
import botocore
import json
import requests
import logging


st.set_page_config(page_title="Kendra Retrieve ChatBot", page_icon=":tada", layout="wide")

#Headers
with st.container():
    st.header("Kendra Retrieve ChatBot")
    st.subheader("Kendra Retrieve ChatBot")
    st.title("Ask Questions against a repository of Documents indexed in Kendra")

#
with st.container():
    st.write("---")
    st.write("### Ask Questions against a repository of Documents indexed in Kendra")
    question = st.text_input("Question")
    st.write("---")



#App Logic
#Search Product
def kendraSearch(question):
    kendra = boto3.client('kendra')
    kendra_response = kendra.retrieve(
    IndexId='ADD INDEX HERE', #ADD YOUR KENDRA INDEX HERE
    QueryText=question,
    PageNumber=1,
    PageSize=15
)
    print(kendra_response)
    return kendra_response




#Invoke LLM
def invokeLLM(question, kendra_response):
    #Setup Bedrock client
    bedrock = boto3.client('bedrock-runtime' , 'us-east-1', endpoint_url='https://bedrock.us-east-1.amazonaws.com')
    #llm = Bedrock(model_id="anthropic.claude-v1", client=bedrock, model_kwargs={'max_tokens_to_sample':2000})
    #bedrock_embeddings = BedrockEmbeddings(client=bedrock)
    modelId = "anthropic.claude-v1"  # change this to use a different version from the model provider
    accept = "application/json"
    contentType = "application/json"





    prompt_data = f"""
Human:

Answer the following question to the best of your ability based on the context provided.
Provide an answer and provide sources and the source link to where the relevant infomration can be found. Include this at the end of the response
Do not include information that is not relevant to the question.
Only provide information based on the context provided, and do not make assumptions
Only Provide the source if relevant information came from that source in your answer
You output should be well formated and easy to read
###
Question: {question}

Context: {kendra_response}
###

Assitant: Based on the context provided

"""
    body = json.dumps({"prompt": prompt_data,
                "max_tokens_to_sample":1000,
                "temperature":0,
                "top_k":250,
                "top_p":0.5,
                "stop_sequences":[]
                })
    response = bedrock.invoke_model(
        body=body, modelId=modelId, accept=accept, contentType=contentType
    )
    response_body = json.loads(response.get('body').read())

    answer=response_body.get('completion')

    return answer



    
#Search Product - invoke from button - start the process
def answer_question(question):

    print('Question = ' + question)
    kendraresults = kendraSearch(question)
    print("Printing Kendra Results")
    print(kendraresults)
    print("---")

    llmresponse = invokeLLM(question,kendraresults)
    print("Printing LLM Response")
    print(llmresponse)
    print("---")

    return llmresponse



result=st.button("Answer Question")
if result:
    st.write(answer_question(question))

#1) Fundtion to get a file from url #

def get_file_from_url(url):
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian
    return local_filename

#funtion to upload image to s3#

def upload_file_to_s3(file_name, bucket, object_name=None):
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True



# Detect labed from image with Rekoginition#

def detect_labels(bucket, key):
    client = boto3.client('rekognition')
    response = client.detect_labels(Image={'S3Object': {'Bucket': bucket, 'Name': key}})
    return response['Labels']

#Function to iterate through a dataframe by time#

def iterate_dataframe_by_time(df, time_col, func):
    for _, row in df.iterrows():
        func(row[time_col])
        

#start a go project#

def start_go_project(project_name, region):
    client = boto3.client('codebuild', region_name=region)
    response = client.start_build(projectName=project_name)
    return response


