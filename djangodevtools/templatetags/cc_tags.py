from django import template

register = template.Library()

def app_module_name(moduleUrl):
    "Return breadcrumb trail leading to URL for this page"
    token = str(moduleUrl).split('/')
    name = (token[-2] + '.' + token[-1])
    return name.split('.py')[0].split('.__init__')[0]

def color_by_cc(cc):
    """
    Risk Evaluation:
      1-10: A simple program, without much risk
     11-20: More complex, moderate risk
     21-50: Complex, high risk program
       >50: Untestable program (very high risk)
    """
    if cc in range(1,10):
        return "#adff2f" #greenyellow
    elif cc in range(11,20):
        return "#add8e6" #lightbue
    elif cc in range(21,50):
        return "orange"
    else:
        return "red"

register.simple_tag(color_by_cc)
register.simple_tag(app_module_name)