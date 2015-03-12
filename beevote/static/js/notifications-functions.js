var _home_notifications = {
	/*
	 group_id: int
	 notifications: int
	 */
	group_notifications: null,
	
	/*
	 group_id: int
	 topic_id: int
	 new_topic: bool
	 new_proposals: int
	 */
	topic_notifications: null
};
function print_groups_notifications() {
	if (_home_notifications.group_notifications != null) {
		$('div.group-well span.notifications').html('');
		$.each(_home_notifications.group_notifications, function(index, notification) {
			$('li.sidebar-group[data-group-id="'+notification.group_id+'"] span.notifications').html('<span class="badge" data-group="'+notification.group_id+'">'+notification.notifications+'</span>');
			$('div.group-well[data-group_id="'+notification.group_id+'"] span.notifications').html('<span class="badge" data-group="'+notification.group_id+'">'+notification.notifications+'</span>');
		});
	}
}
function print_topics_notifications() {
	if (_home_notifications.topic_notifications != null) {
		$('div.topic-item span.notifications').html('');
		$.each(_home_notifications.topic_notifications, function(index, notification) {
			topic_notifications_span = $('div.topic-item[data-group-id="'+notification.group_id+'"][data-topic-id="'+notification.topic_id+'"] span.notifications');
			if (notification.new_topic)
				topic_notifications_span.append('<span class="label label-warning">New</span>');
			if (notification.new_proposals > 0)
				topic_notifications_span.append('<span class="badge" data-group="'+notification.group_id+' data-topic="'+notification.topic_id+'">'+notification.new_proposals+'</span>');
		});
	}
};
function clean_topic_notifications(group_id, topic_id) {
	if (_home_notifications.topic_notifications != null) {
		_home_notifications.topic_notifications = $.grep(_home_notifications.topic_notifications, function(notif, index) {
			if (String(notif.group_id) == String(group_id) && String(notif.topic_id) == String(topic_id)) {
				$.each(_home_notifications.group_notifications, function(i, v) {
					if (v.group_id == group_id)
						v.notifications--;
				});
				return false;
			} else
				return true;
		});
		print_groups_notifications();
		print_topics_notifications();
	}
}
function load_topics_notifications() {
	// jQueryTarget must be like $('span#some_id');
	// $("span.notifications").html('...');
	$.ajax({
		url: "/api/topics-notifications",
		method: "GET",
		dataType: "json",
		success: function(response_notifications) {
			/*
				{
					'group_1_id': {
						'topic_1_id': {
							'topic_creations': int,
							'topic_image_change': int,
							'proposal_creations': int,
							'topic_expirations': int,
						},
						...
					},
					...
					
				}
			 */
			_home_notifications.group_notifications = [];
			_home_notifications.topic_notifications = [];
			$.each(response_notifications, function(group_id, group_notifications) {
				var number_of_group_notifications = 0;
				$.each(group_notifications, function(topic_id, topic_notifications) {
					_home_notifications.topic_notifications.push({
						group_id: group_id,
						topic_id: topic_id,
						new_topic: topic_notifications.topic_creations > 0,
						new_proposals: topic_notifications.proposal_creations
					});
					number_of_group_notifications++;
				});
				_home_notifications.group_notifications.push({group_id: group_id, notifications: number_of_group_notifications});
				
			})
			print_groups_notifications();
			print_topics_notifications();
			setTimeout(
				function() { load_topics_notifications(); },
				60*1000 // 1 minute
			);
		}
	});
}