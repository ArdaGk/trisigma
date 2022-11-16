import optparse

def get_option (opt):
    p = optparse.OptionParser()
    p.add_option('--debug', '-d', default=False)
    (options, args) = p.parse_args()
    options = vars(options)
    if opt in options.keys():
        return options[opt]
