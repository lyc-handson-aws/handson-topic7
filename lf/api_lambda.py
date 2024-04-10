
import boto3, json, os, decimal

PETPATH = '/pets'
GETMETHOD = 'GET'
POSTMETHOD = 'POST'
TABLENAME = os.environ.get('TABLE')


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)


def buildResponse(statusCode, body=None):
    response = {
        "statusCode": statusCode,
        "headers": {
            "Access-Control-Allow-Origin":"*",
            "Contetn-Type": "application/json"
            },  
    }
    if body is not None:
        response['body'] = json.dumps(body, cls=DecimalEncoder)
    return response

def getPets():
    dynamo = boto3.resource('dynamodb')
    table = dynamo.Table(TABLENAME)
    response = table.scan()
    pets = response['Items']
    if len(pets) > 0:
        print(pets)
        body = {
            'pets': pets
        }
    else:
        body = {
            'message': "no pet in stroage yet!"
        }
    return buildResponse(200, body)
        
    
def postPets(petInfo):
    dynamo = boto3.resource('dynamodb')
    table = dynamo.Table(TABLENAME)
    pets = table.scan()['Items']
    if len(pets) > 4:
        return buildResponse(409, {"message":"pet storage is full, maxium 5 pets!"})
    for pet in pets:
        if pet['PetName'] == petInfo['PetName']:
            return buildResponse(409, {"message":"pet " + petInfo['PetName'] + " is alredy in the store!"})
    try:
        table.put_item(Item=petInfo)
        body = {
            "Message": "Put pet to our pet storage sucess",
            "Pet's name": petInfo['PetName'],
            "Pet's food stock": petInfo['Food'],
            "Pet belongs to": petInfo['Owner'],
            "Contact Email": petInfo['Email']
        }
    except:
        return buildResponse(500, {"message": "database problem, pls retry later!"})

    try:
        schedule = os.environ.get('SCHEDULE')
        stepfunction_smarn = os.environ.get('STEPFUNTIONSMARN')
        sm = boto3.client('stepfunctions')
        if len(sm.list_executions(stateMachineArn=stepfunction_smarn,statusFilter='RUNNING')['executions']) == 0:
            sm.start_execution(stateMachineArn=stepfunction_smarn, input=json.dumps({'SchedulerName':schedule}) )
    except Exception as e: 
        print(e)
        return buildResponse(500, {"message": "internal problem, pls retry later!"})
    return buildResponse(200, body)


def lambda_handler(event, context):
    # Print event data to logs .. 
    print("Received event: " + json.dumps(event))

    http_method = event['httpMethod']
    http_path = event['path']
    if http_method == GETMETHOD and http_path == PETPATH:
        response = getPets()
    elif http_method == POSTMETHOD and http_path == PETPATH:
        response = postPets(json.loads(event['body']))
    else: 
        response = buildResponse(404, 'pet storage can\'t do other stuffs!')

    return response




