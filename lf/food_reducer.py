import boto3, os, json
import json


FROM_EMAIL_ADDRESS = os.environ.get('EMAIL')

def lambda_handler(event, context):
    # Initialize DynamoDB client
    dynamo = boto3.resource('dynamodb')
    table_name = os.environ.get('TABLE')
    # Get reference to your DynamoDB table
    table = dynamo.Table(table_name)
    
    # Scan the entire table to fetch all items
    response = table.scan()
    
    # Modify the desired value for each item
    for item in response['Items']:
        # Modify the value of the desired attribute (replace 'old_value' with the actual value you want to modify)
        current_food = int(item['Food'])
        print(item['PetName'] + " of owner " + item['Owner'] + "'s food has " + str(item['Food']) + " food left")
        food = current_food - 1
        item['food'] = food
        if food <= 0:
            print("there is no enough food for "+item['PetName'])
            table.delete_item(
                Key={
                'Owner': item['Owner'],
                'PetName': item['PetName']
                }
            )
            print(item['PetName'] + " of owner " + item['Owner'] + " item is been deleted in the table")
            message = item['PetName'] + "is dead due to the lack of food"
            email_message={ 
                'Subject': {
                      'Data': 'You didn\'t provide enough foods for your pet druing transition period'
                },
                'Body': {
                    'Text': {
                        'Data': "Hello" + item['Owner']+ "\n your pet: " + message
                    }
                }
            }
            ses = boto3.client('ses')
            ses.send_email( Source=FROM_EMAIL_ADDRESS,
            Destination={ 'ToAddresses': [ item['Email'] ] }, 
            Message=email_message)
        else:
            table.update_item(
                Key={
                'Owner': item['Owner'],
                'PetName': item['PetName']
            },
                UpdateExpression='SET Food = :val',
                ExpressionAttributeValues={':val': food}
            )
            print(item['PetName'] + " of owner " + item['Owner'] + "'s food is reduced -1")
