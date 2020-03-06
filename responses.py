def process_input(input):
    if input == '/start':
        return 'Welcome'
    if input == '/stop':
        return 'Goodbye'
    if input.startswith('echo '):
        return input[len('echo '):]
    # Customize your responses here
