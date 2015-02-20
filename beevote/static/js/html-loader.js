function load_groups(opened_group) {
	$('#group-list').html('<div class="loader"></div>');
	if (opened_group == null)
		$('#group-list').load('/html/groups');
	else
		$('#group-list').load('/html/groups', function() {
			$('div.group-well[data-group_id="'+opened_group+'"]').click();
		});
}

// Start of left columns loadings

function load_all_topics() {
	$('div#right-column').html('<div class="loader"></div>');
	$('div#right-column').load('/html/topics', function() {
		$('#creation-buttons').html('');
		$('#creation-buttons').append(buttons.create_group);
	});
}

function load_group_topics(group_id) {
	$('div#right-column').html('<div class="loader"></div>');
	$('div#right-column').load('/html/group/'+group_id, function() {
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
	$('div.group-well').removeClass('group-selected');
	$('div.group-well[data-group_id="'+group_id+'"]').addClass('group-selected');
	$('div#right-column').html('<div class="loader"></div>');
	$('div#right-column').load('/html/group/'+group_id+'/topic/'+topic_id);
}

// End of left columns loadings