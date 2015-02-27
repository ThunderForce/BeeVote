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
			if (typeof additional_callback == "function")
				additional_callback();
		}
	});
}

function load_groups(opened_group) {
	$('#group-list').html('<div class="loader"></div>');
	/* sidebar's ajax */
	$.ajax({
		url: '/api/groups',
		method: "GET",
		success: function(groups) {
			var content = $('ul#sidebar-content');
			$('ul#sidebar-content li:not(.sidebar-home, .sidebar-toggle, .sidebar-brand, .sidebar-logout, .sidebar-feedback, .sidebar-groups)').remove();
			$.each(groups, function(index, group) {
				if (group.data.has_image) {
					content.append('<li class="sidebar-group" data-group-id="'+group.data.id+'" style="cursor: pointer;color:#FFFFFF;font-size:19px;margin-bottom:10px;"><img class="circle" src="/group/'+group.data.id+'/image" alt="icon" style="width:50px;height:50px;border-radius:100%;margin-right:10px;">'+group.data.name+'</li>');
				}
				else {
					content.append('<li class="sidebar-group" data-group-id="'+group.data.id+'" style="cursor: pointer;color:#FFFFFF;font-size:19px;margin-bottom:10px;"><img class="circle" src="/static/images/group-default.jpg" alt="icon" style="width:50px;height:50px;border-radius:100%;margin-right:10px;">'+group.data.name+'</li>');
				}
			});
			//Function to load sidebar group
			$("li.sidebar-group").click(function(e) {
				$("#wrapper").toggleClass("toggled");
				load_group_topics($(this).data('group-id'));
			});
			$("li.sidebar-brand").click(function(e) {
				$("#wrapper").toggleClass("toggled");
				$('#updateUser').modal('show'); //open popup "updateUser"
			});
			$('li.sidebar-toggle').click(function(e) {
				$('#wrapper').toggleClass("toggled");
			});
			$('li.sidebar-home').click(function(e) {
				$('#wrapper').toggleClass("toggled");
				load_all_topics();
			});
		}
	});
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
	_load_right_column('/html/topics');
}

function load_group_topics(group_id) {
	if (window.history.replaceState == null) {
		window.location.href = "/group/"+group_id;
		return
	}
	// better use pushState
	window.history.replaceState(null, "Group", "/group/"+group_id);
	$('div#right-column').html('<div class="loader"></div>');
	_load_right_column('/html/group/'+group_id);
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
	_load_right_column('/html/group/'+group_id+'/topic/'+topic_id, function() {
	});
	$('div.group-well').removeClass('group-selected');
	$('div.group-well[data-group_id="'+group_id+'"]').addClass('group-selected');
}

// End of left columns loadings