from __future__ import print_function
import datetime
import os
import re
import sys
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from wand.color import Color
from wand.image import Image
from wand.drawing import Drawing
try:
    from tinys3 import Connection
except ImportError:
    pass


PASS_THRESHOLD = 0.999
EXAMPLE = """
                                                   *******
                                                  **********
                                                 ***********
                                                *************
                                                *************    ***
                                                ************ ***********
                                                *************************
                                                 *************************
                                  ********        *************************
                                **********          **********************
                             *************           *********************
                             *************          ********************
                       ************************    *******  **********
                   **************************************
                ****************************************
              ********************************************
             **********************************************
            ************************************************
           *************************************************
          ***************************************************
          ****************************************************
         *************   ***************   *******************
         **********   ****  *********  ****  *****************
         ********** ******** ******  ******** ****************
          ******** ********* ****** *********  ***************
          ******** ********** ***** ********** ***************
          ******** ********** ***** ********** ***************
        ********** ********** ***** ********** *****************
       *********** ********* ****** ********** *******************
      ************* ******** *******  *******  ********************
     ****************      ***********       **********************
    ***************************************************************
    ***************************************************************
    ***************************************************************
    ***************************************************************
     *************************************************************
      ***********************************************************
       **********************************************************
        ********************************************************
         *****************************************************
            ************************************************
                ***************************************
"""


def fetch_result():
    text = os.popen('python pupu.py').read()
    return text


def create_image(text):
    split_by_rows = text.split('\n')
    split_by_rows = list(filter(lambda n: len(n.strip()) > 0, split_by_rows))
    rows = len(split_by_rows)
    cols = max(map(lambda n: len(n), split_by_rows))
    image = Image(width=cols, height=rows, background=Color('white'))
    with Drawing() as draw:
        for y, row in enumerate(split_by_rows):
            if len(row.strip()) == 0:
                continue
            for x, point in enumerate(row):
                if point != ' ':
                    draw.point(x, y)
        draw(image)
    return image


def calculate_similarity(a, b):
    pixels = 0
    match = 0
    for ay, by in zip(a, b):
        for apx, bpx in zip(ay, by):
            if (apx == bpx):
                match += 1
            pixels += 1
    return float(match)/pixels


def upload_to_s3(result, similarity):
    aws_access_key = os.getenv('AWS_ACCESS_KEY')
    aws_access_secret = os.getenv('AWS_ACCESS_SECRET')
    if aws_access_key is None or aws_access_secret is None:
        return
    remote = os.popen('git config --get remote.origin.url').read().strip()
    match = re.match('.*/([a-zA-Z0-9_-]+)/spoqa-pycon-2015-codegolf.git', remote)
    if match is None:
        participant = 'unknown'
    else:
        participant = match.group(1)
    now = datetime.datetime.now().strftime('%y%M%d-%H%M%S')
    name = '%s-%s-%d.txt' % (participant, now, similarity * 100)
    conn = Connection(aws_access_key, aws_access_secret,
                      default_bucket='entries',
                      endpoint='pycon-2015-codegolf.s3.amazonaws.com')
    conn.upload(name, StringIO(result))


def do_test():
    result = fetch_result()
    a = create_image(EXAMPLE)
    b = create_image(result)
    similarity = calculate_similarity(a, b)
    try:
        upload_to_s3(result, similarity)
    except:
        pass
    if similarity < PASS_THRESHOLD:
        print('Validation failed. (similarity: %.2f%%)' % (similarity * 100))
        sys.exit(1)
    else:
        print('Passed')


if __name__ == '__main__':
    do_test()
