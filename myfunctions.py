import os,io
from google.cloud import vision
from google.cloud import vision_v1
#from google.cloud.vision import types
from google.cloud.vision_v1 import types
#from google.cloud.vision.types import Image
from google.cloud.vision_v1.types import Image
import pandas as pd
import os
from IPython.display import Image
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def detectText(imag):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_API_KEY")
    client_txt = vision_v1.ImageAnnotatorClient()
    google_ocr_dict={}
        
    with io.open(imag,'rb') as image_file:
        content=image_file.read()
        
    image = vision_v1.Image(content=content)
    response = client_txt.text_detection(image=image)
    texts = response.text_annotations
    text_num = 0
    google_ocr_dict[text_num]= {}
    
    for text in texts:
        # Create a sub-dictionary for each block of text
        google_ocr_dict[text_num] = {}
        # Get the coordinates of the bounding box around the text
        vertices = ([[vertex.x, vertex.y]
                    for vertex in text.bounding_poly.vertices])
        # Add the text and its coordinates to the dictionary
        google_ocr_dict[text_num]['text'] = text.description
        google_ocr_dict[text_num]['coords'] = vertices
        # Increment the text number
        text_num+=1
        
    with open("processed_image_new.json","w") as json_file:
            json.dump(google_ocr_dict,json_file,indent=4)
        
    print(f"Created processed_image.jpg using Google OCR")
    return google_ocr_dict[0]["text"].replace("\n"," ")


#------------------------------------------------------------------------------------------------------------------
def get_info_from_image(imag):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_API_KEY")
    client = vision_v1.ImageAnnotatorClient()
    text = detectText(imag)
    with open("processed_image_new.json", "r") as json_file:
        y = json.load(json_file)
    texts = [item['text'] for item in y.values()]
    
    client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))
    system_role="Extract entities and their values as a key-value pair from the provided OCR text and seperate them by a new line."
    #Get The Response
    ocr_text = texts[0]
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role":"system","content":system_role},
            {"role":"user","content":ocr_text} #pass the OCR Text obtained from 
        ])

    generated_text = response.choices[0].message.content.strip()
    # Split the text into separate lines
    lines = generated_text.split('\n')
    # Initialize an empty dictionary to store key-value pairs
    data_dict = {}

    # Extract key-value pairs from each line
    for line in lines:
        key, value = line.split(': ', 1)
        data_dict[key] = value

    # Create a dataframe from the dictionary
    df = pd.DataFrame.from_dict(data_dict, orient='index', columns=['Value'])

    # Reset index to have a 'Key' column
    df.reset_index(inplace=True)
    df.columns = ['Key', 'Value']

    # Display the dataframe
    return df


#-----------------------------------------------------------------------------------------------------------------------
def get_total_from_image(imag):
    text = detectText(imag)
    with open("processed_image_new.json", "r") as json_file:
        y = json.load(json_file)
    texts = [item['text'] for item in y.values()]
    
    client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))
    #define System Role
    system_role="Extract place name(no more than 30 characters. If None classify as Other.), total to pay (converted to euros, 2 decimal places, using . as a decimal separator and without symbols), type of expense (in one of these types: Grocery, Restaurant, Fuel, Transportation, Entertainment, Insurance, Other. If none classify as Other. With first letter in upper case), date of expense (in format YYYY-MM-DD. if not possible to obtain the date classify as None) and their values as a key-value pair from the provided OCR text and seperate them by a new line."
    #Get The Response
    ocr_text = texts[0]
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role":"system","content":system_role},
            {"role":"user","content":ocr_text} #pass the OCR Text obtained from 
        ])

    generated_text = response.choices[0].message.content.strip()
    lines = generated_text.split('\n')

    # Initialize variables to store extracted information
    place = None
    total_to_pay = None
    type_of_expense = None
    date_of_expense = None

    # Iterate through the lines to extract information            
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)  # Split at the first colon only
            key = key.strip()  # Remove any leading or trailing spaces
            value = value.strip()  # Remove any leading or trailing spaces

        # Assign values based on the keys
            if key.lower() == 'place':
                place = value
            elif key.lower() == 'total to pay':
                total_to_pay = value
            elif key.lower() == 'type of expense':
                type_of_expense = value
            elif key.lower() == 'date of expense':
                date_of_expense = value

        # Create a dataframe from the extracted information
    df = pd.DataFrame({
        'Place': [place],
        'Total to Pay': [total_to_pay],
        'Type of Expense': [type_of_expense],
        'Date of Expense': [date_of_expense]
    })
    
    #df = df.dropna(subset=['Total to Pay', 'Date of Expense'], inplace=True)

    return df
