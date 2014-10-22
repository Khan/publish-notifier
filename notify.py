import contextlib
import json
import socket
import time
import urllib2

import hipchat.config
import hipchat.room

import secrets

hipchat.config.token = secrets.hipchat_token


def hipchat_notify(room_ids, message):
    # Pure kwargs don't work here because 'from' is a Python keyword...
    for room_id in room_ids:
        hipchat.room.Room.message(**{
            'room_id': room_id,
            'from': 'Publish Primate',
            'message': message,
            'color': 'purple',
        })


def get_publish(
        url='http://www.khanacademy.org/api/internal/dev/publish_status'):
    try:
        with contextlib.closing(urllib2.urlopen(url)) as f:
            data = json.loads(f.read())
    except urllib2.URLError, e:
        print "Couldn't get version: %s" % e
        if isinstance(e, urllib2.HTTPError):
            # When urlllib2 returns an HTTPError, the textual response returned
            # by read() can be helpful when debugging.
            print e.read()
        return None
    except socket.error, e:
        print "Couldn't get version: socket error %s" % e
        return None

    return data


def build_message(publish, publish_status):
    output = ['Publish task %s (%s): %s.' % (
        publish["status_id"], publish["type"], publish_status)]

    if not publish["active"]:
        output.append('&bull; Duration: %s' % publish["duration"])
    if publish["owner"] != publish["commit_owner"]:
        output.append('&bull; Published by: %s' % publish["owner"])
    output.append('&bull; Commit: %s' % publish["commit_sha"])
    output.append('&bull; Committer: %s' % publish["commit_owner"])
    output.append('&bull; Commit message: %s' % publish["commit_message"])
    # TODO(dylan): Also report subject/tutorial titles in the message
    return "<br>".join(output)

if __name__ == '__main__':
    hipchat_notify(
        secrets.hipchat_room_ids,
        'Restarting notify.py!')

    last_publish_id = None
    last_publish_status = None
 
    while True:
        publish = get_publish()

        if publish is not None:
            publish_status = "started"
            if not publish["active"]:
                publish_status = (
                    "completed successfully" if publish["success"]
                    else "failed")
                print "%s: %s" % (publish["status_id"], publish_status)

            if (last_publish_id is not None
                and (publish["status_id"] != last_publish_id or
                    publish_status != last_publish_status)):
                hipchat_notify(
                    secrets.hipchat_room_ids,
                    build_message(publish, publish_status))
            last_publish_id = publish["status_id"]
            last_publish_status = publish_status
        else:
            print "No publish received"

        time.sleep(10)
