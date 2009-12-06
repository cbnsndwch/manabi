from django import template

register = template.Library()

class XhrLinkNode(Node):
    def __init__(self, filepath, parsed):
        self.filepath, self.parsed = filepath, parsed

    def render(self, context):
        if not include_is_allowed(self.filepath):
            if settings.DEBUG:
                return "[Didn't have permission to include file]"
            else:
                return '' # Fail silently for invalid includes.
        try:
            fp = open(self.filepath, 'r')
            output = fp.read()
            fp.close()
        except IOError:
            output = ''
        if self.parsed:
            try:
                t = Template(output, name=self.filepath)
                return t.render(context)
            except TemplateSyntaxError, e:
                if settings.DEBUG:
                    return "[Included template had syntax error: %s]" % e
                else:
                    return '' # Fail silently for invalid included templates.
        return output


def xhrlink(parser, token):
    """
    """
    bits = token.contents.split()
    parsed = False
    if len(bits) not in (2,):
        raise TemplateSyntaxError('Wrong number of arguments for xhrlink')
    if len(bits) == 3:
        if bits[2] == 'parsed':
            parsed = True
        else:
            raise TemplateSyntaxError("Second (optional) argument to %s tag"
                                      " must be 'parsed'" % bits[0])
    return SsiNode(bits[1], parsed)
ssi = register.tag(ssi)

