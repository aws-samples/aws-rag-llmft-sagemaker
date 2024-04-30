from utils.llm_wrapper import sagemaker_llm
from utils.opensearch_client import docsearch, VectorStoreRetrieverWithScore
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory

sm_llm = sagemaker_llm

memory = ConversationBufferWindowMemory(k=3, 
                                        memory_key="chat_history", 
                                        return_messages=True,
                                        input_key='question',
                                        output_key='answer',)

def chat(question: str):

    retriever = VectorStoreRetrieverWithScore(
        vectorstore=docsearch,
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": 0.5, "k": 3},
        )
    
    qa = ConversationalRetrievalChain.from_llm(sm_llm, 
                                           retriever, 
                                           memory=memory,
                                           return_source_documents=True)
    
    result = qa({"question": question})
    
    answer = result["answer"]

    sources = "**You can refer to further explanations in the following resources:** \n"
    for d in result['source_documents']:
        filename = d.metadata['source'].split("./TestingResources/")[1]
        current_file = '* ' + filename + " - page: " + str(d.metadata['page']) + "\n"
        sources += current_file

    if len(result['source_documents']) > 0:
        score = '**RAG - Score: ' + str(int(result['source_documents'][0].metadata['score']*100)) + '%**'
    else:
        score = 'No resources found.'
        sources = ""

    output = answer + "\n\n" + score + "\n\n" + sources

    return output

def clear_memory():
    memory.clear()