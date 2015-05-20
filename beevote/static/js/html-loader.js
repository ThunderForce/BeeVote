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
		},
		statusCode: {
			401: function() {
				alert("You don't have permission to view this group. You'll be redirected to home page.");
				load_all_topics();
			},
			500: function() {
				$('div#right-column').html("" +
						"<p>Internal server error.</p>" +
						"<p>Try to refresh the page.</p>" +
						"<p>If the problem persists contact us.</p>");
			}
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
			$('ul#sidebar-content li:not(.sidebar-home, .sidebar-toggle, .sidebar-brand, .sidebar-logout, .sidebar-feedback, .sidebar-bug-report, .sidebar-groups)').remove();
			$.each(groups, function(index, group) {
				var group_name = group.data.name;
				if (group_name.length>15) {
					group_name = group_name.substring(0, 12)+"...";
				}
				if (group.data.has_image) {
					content.append('<li class="sidebar-group" data-group-id="'+group.data.id+'" style="cursor: pointer;color:#FFFFFF;font-size:19px;margin-bottom:10px;"><img class="circle" src="/group/'+group.data.id+'/image?width=64&height=64" alt="icon" style="width:40px;height:40px;border-radius:100%;margin-right:10px;">'+group_name+' <span class="notifications">...</span></li>');
				}
				else {
					content.append('<li class="sidebar-group" data-group-id="'+group.data.id+'" style="cursor: pointer;color:#FFFFFF;font-size:19px;margin-bottom:10px;"><img class="circle" src="/static/images/group-default.jpg" alt="icon" style="width:40px;height:40px;border-radius:100%;margin-right:10px;">'+group_name+' <span class="notifications">...</span></li>');
				}
			});
			//Function to load sidebar group
			$("li.sidebar-group").unbind("click");
			$("li.sidebar-group").click(function(e) {
				$("#wrapper").toggleClass("toggled");
				load_group_topics($(this).data('group-id'));
			});
			$("li.sidebar-brand").unbind("click");
			$("li.sidebar-brand").click(function(e) {
				$("#wrapper").toggleClass("toggled");
				$('#updateUser').modal('show'); //open popup "updateUser"
			});
			$('li.sidebar-toggle').unbind("click");
			$('li.sidebar-toggle').click(function(e) {
				$('#wrapper').toggleClass("toggled");
			});
			$('li.sidebar-home').unbind("click");
			$('li.sidebar-home').click(function(e) {
				$('#wrapper').toggleClass("toggled");
				load_all_topics();
			});
		}
	});
	$.ajax({
		url: '/html/groups',
		method: "GET",
		success: function(response) {
			$('div#group-list').html(response);
			if (opened_group != null) {
				$('div.group-well').removeClass('group-selected');
				$('div.group-well[data-group_id="'+opened_group+'"]').addClass('group-selected');
			}
		},
		statusCode: {
			500: function() {
				$('div#group-list').html("" +
						"<p>Internal server error.</p>" +
						"<p>Try to refresh the page.</p>" +
						"<p>If the problem persists contact us.</p>");
			}
		}
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
	window.history.replaceState(null, "Topic", "/group/"+group_id+"/topic/"+topic_id);
	$('div#right-column').html('<div class="loader"></div>');
	_load_right_column('/html/group/'+group_id+'/topic/'+topic_id, function() {
	});
	$('div.group-well').removeClass('group-selected');
	$('div.group-well[data-group_id="'+group_id+'"]').addClass('group-selected');
}

// End of left columns loadings