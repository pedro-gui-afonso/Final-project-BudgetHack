from flask import Flask, request, render_template, redirect, url_for
from myfunctions import get_info_from_image, get_total_from_image
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from splitting import Budgethack


app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global variable to store uploaded bills data
uploaded_bills = []
transactions = []

@app.route('/')
def index():
    return render_template('index2c.html')

@app.route('/start')
def start():
    return render_template('index2a.html', uploaded_bills=bool(uploaded_bills))

@app.route('/upload', methods=['POST'])
def upload_file():
    global uploaded_bills
    
    if 'files' not in request.files:
        return {'error': 'No file part'}, 400

    files = request.files.getlist('files')  # Get the list of files

    if not files or files[0].filename == '':
        return {'error': 'No selected file'}, 400

    uploaded_bills = []  # Reset uploaded bills
    for file in files:
        if file:  # Check if the file exists
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Apply OCR and get information from the uploaded image
            # Assuming get_total_from_image returns a DataFrame with relevant information
            df = get_total_from_image(file_path)
            
            # Optionally, add a column to df to indicate the source file
            #df['Source'] = filename
            
            uploaded_bills.append(df)
            
    cleaned_dataframes = []
    
    for df in uploaded_bills:
        cleaned_df = df.dropna(subset=['Total to Pay'])
        cleaned_df = cleaned_df.dropna(subset=['Date of Expense'])
        cleaned_dataframes.append(cleaned_df)
    
    uploaded_bills=cleaned_dataframes   
    #print(uploaded_bills)
    #uploaded_bills = [df.dropna(subset=['Total to Pay', 'Date of Expense']) for df in uploaded_bills if df is not None]
    return redirect(url_for('display_options'))


@app.route('/display_options')
def display_options():
    return render_template('index2b.html', uploaded_bills=bool(uploaded_bills))


@app.route('/display_graph2', methods=['GET', 'POST'])
def display_graph2():
    if uploaded_bills:
        # Concatenate all DataFrames into one
        total_df = pd.concat(uploaded_bills, ignore_index=True)
        type_of_expenses = total_df['Type of Expense'].unique().tolist()
        total_df['Total to Pay'] = pd.to_numeric(total_df['Total to Pay'], errors='coerce').round(2)

        if request.method == 'POST':
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            selected_types = request.form.getlist('expense_type')  # Get list of selected expense types

            # Filter data based on selected date range
            filtered_df = total_df.copy()
            if start_date and end_date:
                filtered_df = filtered_df[(filtered_df['Date of Expense'] >= start_date) & (filtered_df['Date of Expense'] <= end_date)]

            # Filter data based on selected expense types
            if selected_types:
                filtered_df = filtered_df[filtered_df['Type of Expense'].isin(selected_types)]

            
            # Calculate expenses by type for the filtered data
            expenses_by_type = filtered_df.groupby('Type of Expense')['Total to Pay'].sum().round(2)

            img = io.BytesIO()

            # Create a pie chart
            plt.figure(figsize=(6, 6), facecolor='lightgray')
            plt.pie(expenses_by_type, labels=expenses_by_type.index, autopct='%1.1f%%', startangle=140)
            #plt.title('Expenses by Type')
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            plt.savefig(img, format='png')  # Save the plot directly to the BytesIO buffer
            plt.close()  # Close the plot to free memory

            # Encode the image data to base64 format
            graph_url = base64.b64encode(img.getvalue()).decode()

            # Reset the buffer position to the beginning
            img.seek(0)

            expenses_by_date = filtered_df.copy()
            # Convert 'Date of Expense' column to datetime format
            expenses_by_date['Date of Expense'] = pd.to_datetime(expenses_by_date['Date of Expense'])

            expenses_by_date['Year'] = expenses_by_date['Date of Expense'].dt.year
            expenses_by_type_year = expenses_by_date.groupby(['Year','Type of Expense'])['Total to Pay'].sum().unstack()
            
            # Create a stacked bar chart
            fig, ax = plt.subplots(figsize=(5, 5))
            expenses_by_type_year.plot(kind='bar', stacked=True, ax=ax)
            ax.set_facecolor('lightblue')
            fig.set_facecolor('lightblue')
            # Set the x-axis label and rotation
            plt.xlabel('Year')
            plt.xticks(rotation=45)
            plt.tight_layout()
            img3 = io.BytesIO()
            plt.savefig(img3, format='png')  # Save the plot directly to the BytesIO buffer
            plt.close()  # Close the plot to free memory
            # Encode the image data to base64 format
            graph_url3 = base64.b64encode(img3.getvalue()).decode()
            img3.seek(0)


            fig, ax = plt.subplots(figsize=(5, 5))
            expenses_by_type_year.plot(marker='o', linestyle='-', ax=ax)
            ax.set_facecolor('lightblue')
            fig.set_facecolor('lightblue')
            plt.grid(True)
            plt.tight_layout()
            img2 = io.BytesIO()
            plt.savefig(img2, format='png')  # Save the plot directly to the BytesIO buffer
            plt.close()  # Close the plot to free memory
            # Encode the image data to base64 format
            graph_url2 = base64.b64encode(img2.getvalue()).decode()
            # Reset the buffer position to the beginning
            img2.seek(0)
            graph_url2 = base64.b64encode(img2.getvalue()).decode()
            
            # Display results with filtered data
            return render_template('result2a.html', total_df=filtered_df, graph_url=graph_url, graph_url2=graph_url2, graph_url3=graph_url3, start_date=start_date, end_date=end_date, type_of_expenses=type_of_expenses, expenses_by_type=expenses_by_type)

        # Calculate expenses by type for all data
        expenses_by_type = total_df.groupby('Type of Expense')['Total to Pay'].sum().round(2)
        #print(expenses_by_type)
        img = io.BytesIO()

        # Create a pie chart
        plt.figure(figsize=(6, 6), facecolor='lightgray')
        plt.pie(expenses_by_type, labels=expenses_by_type.index, autopct='%1.1f%%', startangle=140)
        #plt.title('Expenses by Type')
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.savefig(img, format='png')  # Save the plot directly to the BytesIO buffer
        plt.close()  # Close the plot to free memory

        # Encode the image data to base64 format
        graph_url = base64.b64encode(img.getvalue()).decode()

        # Reset the buffer position to the beginning
        img.seek(0)

        expenses_by_date = total_df
        # Convert 'Date of Expense' column to datetime format
        expenses_by_date['Date of Expense'] = pd.to_datetime(expenses_by_date['Date of Expense'])
        
        expenses_by_date['Year'] = expenses_by_date['Date of Expense'].dt.year
        expenses_by_type_year = expenses_by_date.groupby(['Year','Type of Expense'])['Total to Pay'].sum().unstack()
        
        # Create a stacked bar chart
        fig, ax = plt.subplots(figsize=(5, 5))
        expenses_by_type_year.plot(kind='bar', stacked=True, ax=ax)
        ax.set_facecolor('lightblue')
        fig.set_facecolor('lightblue')
        # Set the x-axis label and rotation
        plt.xlabel('Year')
        plt.xticks(rotation=45)
        plt.tight_layout()
        img3 = io.BytesIO()
        plt.savefig(img3, format='png')  # Save the plot directly to the BytesIO buffer
        plt.close()  # Close the plot to free memory
        # Encode the image data to base64 format
        graph_url3 = base64.b64encode(img3.getvalue()).decode()
        img3.seek(0)
        
        # Set 'Date of Expense' column as the index
        #expenses_by_date.set_index('Date of Expense', inplace=True)
        # Sort DataFrame by index (date)
        #expenses_by_date.sort_index(inplace=True)
        fig, ax = plt.subplots(figsize=(5, 5))
        expenses_by_type_year.plot(marker='o', linestyle='-', ax=ax)
        ax.set_facecolor('lightblue')
        fig.set_facecolor('lightblue')
        plt.grid(True)
        plt.tight_layout()
        img2 = io.BytesIO()
        plt.savefig(img2, format='png')  # Save the plot directly to the BytesIO buffer
        plt.close()  # Close the plot to free memory
        graph_url2 = base64.b64encode(img2.getvalue()).decode()

        # Display results with date selector
        return render_template('result2a.html', total_df=total_df, graph_url=graph_url, graph_url2=graph_url2, graph_url3=graph_url3, start_date=None, end_date=None, type_of_expenses=type_of_expenses, expenses_by_type=expenses_by_type)
    else:
        return 'No bills uploaded.'
    
@app.route('/split_bills')
def split_bills():
    if uploaded_bills:
        # Concatenate all DataFrames into one
        total_df = pd.concat(uploaded_bills, ignore_index=True)

        # Display results
        return render_template('result2b.html', total_df=total_df)
    else:
        return 'No bills uploaded.'

@app.route('/allocate_bills', methods=['POST'])
def allocate_bills():
    global uploaded_bills
    global transactions

    if uploaded_bills:
        # Retrieve payer information for each bill
        payer_info = {}
        for index, _ in enumerate(uploaded_bills):
            payer_key = 'payer{}'.format(index)
            payer = request.form.get(payer_key)
            payer_info[index] = payer

        # Associate payer information with each bill and create list of tuples (member, expense)
        expenses = []
        for index, df in enumerate(uploaded_bills):
            payer = payer_info.get(index)
            # Assuming 'Total to Pay per person' column contains expenses
            member_expenses = [(payer, float(row['Total to Pay'])) for _, row in df.iterrows()]
            expenses.extend(member_expenses)   

        # Instantiate the Splitwise class with the list of expenses
        budgethack = Budgethack(expenses)

        # Call the split_expense method to get transactions
        transactions = budgethack.split_expense()
        print(transactions)

        # Clear uploaded_bills after allocation
        uploaded_bills.clear()

        # Redirect to a different route after allocating bills
        return redirect(url_for('display_transactions'))

    return redirect(url_for('index'))  # Redirect to the index route if there are no uploaded bills

@app.route('/display_transactions')
def display_transactions():  
    global transactions
    return render_template('transactions.html', transactions=transactions)  

if __name__ == '__main__':
    app.run(debug=True)
