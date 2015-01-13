function load_votes(group, topic, proposal, success_callback) {
	$.ajax({
		url: "/api/load-votes",
		method: "GET",
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
function add_vote(group, topic, proposal) {
	$("#number_of_votes").html("...");
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
			$("#number_of_votes").html(response.vote_number);
		}
	});
}
function remove_vote(group, topic, proposal) {
	$("#number_of_votes").html("...");
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
			$("#number_of_votes").html(response.vote_number);
		}
	});
}