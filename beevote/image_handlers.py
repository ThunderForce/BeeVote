import logging
import traceback

from google.appengine.api.images import Image

import base_handlers
import models


def resize_image(image_data, width, height):
    image = Image(image_data=image_data)
    if (image.width / float(width)) > (image.height / float(height)):
        image.resize(height=height)
        image = Image(image_data=image.execute_transforms())
        x_crop_ratio = (image.width - width) / float(image.width * 2)
        image.crop(x_crop_ratio, 0.0, 1-x_crop_ratio, 1.0)
    else:
        image.resize(width=width)
        image = Image(image_data=image.execute_transforms())
        y_crop_ratio = (image.height - height) / float(image.height * 2)
        image.crop(0.0, y_crop_ratio, 1.0, 1-y_crop_ratio)
    return image.execute_transforms()

class UserImageHandler(base_handlers.BaseImageHandler):
    def get(self, user_id):
        user = models.BeeVoteUser.get_from_id(long(user_id))
        if user is None:
            self.error(404)
            self.response.out.write("User "+user_id+" does not exist")
        else:
            if user.img is not None:
                self.response.headers['Content-Type'] = 'image/png'
                self.response.headers['Content-Disposition'] = 'inline; filename="user-'+user_id+'.png"'
                width_str = self.request.get('width', None)
                height_str = self.request.get('height', None)
                if width_str is None or height_str is None:
                    self.response.out.write(user.img)
                else:
                    try:
                        width = int(width_str)
                        height = int(height_str)
                        self.response.out.write(resize_image(user.img, width, height))
                    except:
                        stacktrace = traceback.format_exc()
                        logging.error("%s", stacktrace)
                        self.response.out.write(user.img)
            else:
                self.error(404)
                self.response.out.write("User "+user_id+" does not have an image")

class GroupImageHandler(base_handlers.BaseImageHandler):
    def get(self, group_id):
        group = models.Group.get_from_id(long(group_id))
        if group is None:
            self.error(404)
            self.response.out.write("Group "+group_id+" does not exist")
        else:
            if group.img is not None:
                self.response.headers['Content-Type'] = 'image/png'
                self.response.headers['Content-Disposition'] = 'inline; filename="group-'+group_id+'.png"'
                width_str = self.request.get('width', None)
                height_str = self.request.get('height', None)
                if width_str is None or height_str is None:
                    self.response.out.write(group.img)
                else:
                    try:
                        width = int(width_str)
                        height = int(height_str)
                        self.response.out.write(resize_image(group.img, width, height))
                    except:
                        stacktrace = traceback.format_exc()
                        logging.error("%s", stacktrace)
                        self.response.out.write(group.img)
            else:
                self.error(404)
                self.response.out.write("Group "+group_id+" does not have an image")

class TopicImageHandler(base_handlers.BaseImageHandler):
    def get(self, group_id, topic_id):
        topic = models.Topic.get_from_id(long(group_id), long(topic_id))
        if topic is None:
            self.error(404)
            self.response.out.write("Topic "+topic_id+" does not exist")
        else:
            if topic.img is not None:
                self.response.headers['Content-Type'] = 'image/png'
                self.response.headers['Content-Disposition'] = 'inline; filename="topic-'+group_id+'-'+topic_id+'.png"'
                width_str = self.request.get('width', None)
                height_str = self.request.get('height', None)
                if width_str is None or height_str is None:
                    self.response.out.write(topic.img)
                else:
                    try:
                        width = int(width_str)
                        height = int(height_str)
                        self.response.out.write(resize_image(topic.img, width, height))
                    except:
                        stacktrace = traceback.format_exc()
                        logging.error("%s", stacktrace)
                        self.response.out.write(topic.img)
            else:
                self.error(404)
                self.response.out.write("Topic "+topic_id+" does not have an image")