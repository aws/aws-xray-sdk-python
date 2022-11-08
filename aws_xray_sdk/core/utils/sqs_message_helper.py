class SqsMessageHelper:
    
    @staticmethod 
    def isSampled(sqs_message):
        attributes = sqs_message['attributes']

        if 'AWSTraceHeader' not in attributes:
            return False

        return 'Sampled=1' in attributes['AWSTraceHeader']