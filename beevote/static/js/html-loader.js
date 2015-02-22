var ajax_control = {
	right_load: null
};

function _load_right_column(url, additional_callback) {
	if (ajax_control.right_load != null)
		ajax_control.right_load.abort();
	ajax_control.right_load = $.ajax({
		url: url,
		method: "GET",
		success: function(response) {
			$('div#right-column').html(response);
			additional_callback();
		}
	});
}

function load_groups(opened_group) {
	$('#group-list').html('<div class="loader"></div>');
	if (opened_group == null)
		$('#group-list').load('/html/groups');
	else
		$('#group-list').load('/html/groups', function() {
			$('div.group-well').removeClass('group-selected');
			$('div.group-well[data-group_id="'+opened_group+'"]').addClass('group-selected');
//			$('div.group-well[data-group_id="'+opened_group+'"]').click();
		});
}

// Start of left columns loadings

function load_all_topics() {
	if (window.history.replaceState == null) {
		window.location.href = "/home";
		return
	}
	// better use pushState
	window.history.replaceState(null, "Home", "/home");
	$('div#right-column').html('<div class="loader"></div>');
	_load_right_column('/html/topics', function() {
		$('#creation-buttons').html('');
		$('#creation-buttons').append(buttons.create_group);
	});
}

function load_group_topics(group_id) {
	if (window.history.replaceState == null) {
		window.location.href = "/group/"+group_id;
		return
	}
	// better use pushState
	window.history.replaceState(null, "Group", "/group/"+group_id);
	$('div#right-column').html('<div class="loader"></div>');
	_load_right_column('/html/group/'+group_id, function() {
		$('#creation-buttons').html('');
		$('#creation-buttons').append(buttons.create_topic);
		$('#creation-buttons').append(buttons.create_group);
	});
	$('div#member_list:not(div.group-overview div#member-list)').html('<div class="loader"></div>');
	$('div#member_list:not(div.group-overview div#member-list)').load('/html/group/'+group_id+'/members');
	$('form#add-member-form').attr('action', '/api/group/'+group_id+'/members/add');
	$('#groupId').val(group_id);
}

function load_topic(group_id, topic_id) {
	if (window.history.replaceState == null) {
		window.location.href = "/group/"+group_id+"/topic/"+topic_id;
		return
	}
	// better use pushState
	window.history.replaceState(null, "Group", "/group/"+group_id+"/topic/"+topic_id);
	$('div#right-column').html('<div class="loader"></div>');
	_load_right_column('/html/group/'+group_id+'/topic/'+topic_id);
	$('div.group-well').removeClass('group-selected');
	$('div.group-well[data-group_id="'+group_id+'"]').addClass('group-selected');
}

// End of left columns loadings