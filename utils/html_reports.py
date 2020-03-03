import os
from jinja2 import Environment, PackageLoader, select_autoescape

FILE_PATH = os.path.dirname(os.path.abspath(__file__))
REPORTS_FP = os.path.join(os.path.dirname(FILE_PATH), "reports")


def main(report_name, save=False, **kwargs):
    env = Environment(
        loader=PackageLoader('slack_track', 'templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('basic_report.html')
    if save:
        if not os.path.exists(REPORTS_FP):
            os.mkdir(REPORTS_FP)
        template.stream(**kwargs).dump(os.path.join(REPORTS_FP, f"{report_name}.html"))
    else:
        return template.render(**kwargs)


if __name__ == '__main__':
    print(main("BASIC", title="Basic"))
