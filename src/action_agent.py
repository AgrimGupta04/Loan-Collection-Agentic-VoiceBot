from src.services import mcp_service

class Action_agent:
    """
    The hands of teh opperation.

    This agent is stateless and simply executes concrete action (like sending ans SMS)
    when told to do so by the orchestrator (server.py).
    It uses the mcp_service to interact with expernal APIs
    """

    def __init__(self):
        print(" Action_agent initialized.")

    def execute_action(self, action_plan: dict, customer_phone: str) -> bool | dict | None:
        """
        A central method to execute an action based on a plan from the DialogueAgent.

        Args:
            action_plan (dict): A dictionary describing the action, e.g., 
                                {'type': 'SEND_SMS', 'message': 'Hello'}.
            customer_phone (str): The phone number of the customer.

        Returns:
            bool: True if the action was successful, False otherwise.
        """

        action_type = action_plan.get("type")

        if action_type == "SEND_SMS":
            message = action_plan.get("message", "You have a new message.")
            return self._send_sms(customer_phone, message)

        elif action_type == "LOOKUP_NUMBER":
            return self._lookup_number(customer_phone)
        else:
            print(f"Unknown action type: {action_type}")
            return False
        
    def _send_sms(self, to_number: str, message: str) -> bool:
        """
        Private method to handle the SMS sending action.
        It calls the mcp_service to do the actual work.
        """

        print(f"ActionAgent: Executing send_sms to {to_number}")

        success = mcp_service.send_sms(to_number, message)
        return success
    
    def _lookup_number(self, phone_number: str) -> dict | None:
        """
        Private method to handle phone number lookup action.
        It calls the mcp_service to do the actual work.
        """

        print(f"ActionAgent: Executing lookup_number for {phone_number}")

        info = mcp_service.lookup_number(phone_number)
        return info
    

if __name__ == "__main__":
    agent = Action_agent()
    print("Action_agent test successful!")