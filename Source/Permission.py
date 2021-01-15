class Permission(self, commandList):
    #commandList is a list of commands they are allowed to execute.
    commandList = []
    def __init__(self, commandList):
        self.commandList = commandList

    def canRun(command):
        if command in commandList:
            return True
        else:
            return False