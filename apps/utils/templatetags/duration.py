# Import template library
from django import template

# Set register
register = template.Library()


FUZZ_LIMIT = 2


@register.filter
def days_to_duration(value, arg=''):
    '''
    Same as `seconds_to_duration` except for inputting floating-point days.
    '''
    if value is None:
        return ''

    secs = float(value) * 24 * 60 * 60
    return seconds_to_duration(secs, arg=arg)


# Register filter
@register.filter
def seconds_to_duration(value, arg=''):
    
    """
    #######################################################
    #                                                     #
    #   Seconds-to-Duration Template Tag                  #
    #   Dan Ward 2009 (http://d-w.me)                     #
    #                                                     #
    #######################################################
    
    Usage: {{ VALUE|seconds_to_duration[:"long"] }}
    
    NOTE: Please read up 'Custom template tags and filters'
          if you are unsure as to how the template tag is
          implemented in your project.
    """
    if value is None:
        return ''

    # Place seconds in to integer
    secs = int(float(value))
    
    args = [e.strip() for e in arg.split(',')]
    do_long = 'long' in args
    do_fuzz = 'fuzz' in args

    parts = 0

    def fuzz_maxed():
        if do_fuzz:
            return parts >= FUZZ_LIMIT
        return False
    
    # Place durations of given units in to variables
    daySecs = 86400
    hourSecs = 3600
    minSecs = 60
    
    # If short string is enabled
    if not do_long:
        
        # Set short names
        dayUnitName = ' day'
        hourUnitName = ' hr'
        minUnitName = ' min'
        secUnitName = ' sec'
        
        # Set short duration unit splitters
        lastDurSplitter = ' '
        nextDurSplitter = lastDurSplitter
    
    # If short string is not provided or any other value
    else:
        
        # Set long names
        dayUnitName = ' day'
        hourUnitName = ' hour'
        minUnitName = ' minute'
        secUnitName = ' second'
        
        # Set long duration unit splitters
        #lastDurSplitter = ' and '
        lastDurSplitter = ', '
        nextDurSplitter = ', '

    if secs == 0 and float(value) > 0:
        return 'under a second'

    # If seconds are greater than 0
    if secs > 0:
        
        # Import math library
        import math
        
        
        # Create string to hold outout
        durationString = ''
        
        # Calculate number of days from seconds
        days = int(math.floor(secs / int(daySecs)))
        
        # Subtract days from seconds
        secs = secs - (days * int(daySecs))
        
        # Calculate number of hours from seconds (minus number of days)
        hours = int(math.floor(secs / int(hourSecs)))
        
        # Subtract hours from seconds
        secs = secs - (hours * int(hourSecs))
        
        # Calculate number of minutes from seconds (minus number of days and hours)
        minutes = int(math.floor(secs / int(minSecs)))
        
        # Subtract days from seconds
        secs = secs - (minutes * int(minSecs))
        
        # Calculate number of seconds (minus days, hours and minutes)
        seconds = secs
        
        # If number of days is greater than 0               
        if days > 0:
            # Add multiple days to duration string
            durationString += ' ' + str(days) + dayUnitName + (days > 1 and 's' or '')
            parts += 1
        
        # Determine if next string is to be shown
        if hours > 0 and not fuzz_maxed():
            # If there are no more units after this
            if minutes <= 0 and seconds <= 0 and len(durationString):
                # Set hour splitter to last
                hourSplitter = lastDurSplitter

            # If there are unit after this
            else:
                # Set hour splitter to next
                hourSplitter = (len(durationString) > 0 and nextDurSplitter or '')
        
            # Add multiple days to duration string
            durationString += hourSplitter + ' ' + str(hours) + hourUnitName + (hours > 1 and 's' or '')
            parts += 1
        
        # Determine if next string is to be shown
        if minutes > 0 and not fuzz_maxed():
            # If there are no more units after this
            if seconds <= 0 and len(durationString):
                # Set minute splitter to last
                minSplitter = lastDurSplitter
            
            # If there are unit after this
            else:
                # Set minute splitter to next
                minSplitter = (len(durationString) > 0 and nextDurSplitter or '')

            # Add multiple days to duration string
            durationString += minSplitter + ' ' + str(minutes) + minUnitName + (minutes > 1 and 's' or '')
            parts += 1
        
        # Determine if next string is last
        if seconds > 0 and not fuzz_maxed():
            # Set second splitter
            secSplitter = (len(durationString) > 0 and lastDurSplitter or '')
        
            # Add multiple days to duration string
            durationString += secSplitter + ' ' + str(seconds) + secUnitName + (seconds > 1 and 's' or '')
            
        # Return duration string
        return durationString.strip()
        
    # If seconds are not greater than 0
    else:
        # Provide 'No duration' message
        return 'No duration'
    


