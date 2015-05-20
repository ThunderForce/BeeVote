function load_votes(group, topic, proposal, success_callback) {
	$.ajax({
		url: "/api/group/"+group+"/topic/"+topic+"/proposal/"+proposal,
		method: "GET",
		data: {
			fetch_votes: true,
			fetch_users: true
		},
		dataType: "json",
		success: function(response) {
			success_callback(response);
		}
	});
}
function add_vote(group, topic, proposal, success_callback) {
	$.ajax({
		url: "/api/create-vote",
		method: "POST",
		data: {
			group_id: group,
			topic_id: topic,
			proposal_id: proposal
		},
		dataType: "json",
		success: function(response) {
			success_callback(response);
		}
	});
}
function remove_vote(group, topic, proposal, success_callback) {
	$.ajax({
		url: "/api/remove-vote",
		method: "POST",
		data: {
			group_id: group,
			topic_id: topic,
			proposal_id: proposal
		},
		dataType: "json",
		success: function(response) {
			success_callback(response);
		}
	});
}