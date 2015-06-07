import base_handlers
import constants
import models


class UserImageHandler(base_handlers.BaseImageHandler):
    def get(self, user_id):
        user = models.BeeVoteUser.get_from_id(long(user_id))
        if user is None:
            self.error(404)
            self.response.out.write("User "+user_id+" does not exist")
        else:
            if user.img is not None:
                self.write_image(user.img, constants.user_image_name.format(user_id=user_id))
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
                self.write_image(group.img, constants.user_image_name.format(group_id=group_id))
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
                self.write_image(topic.img, constants.user_image_name.format(group_id=group_id, topic_id=topic_id))
            else:
                self.error(404)
                self.response.out.write("Topic "+topic_id+" does not have an image")