/**
 * Shared ballot candidate management functions.
 * Used by both vote.html (fallback) and meeting.html modal interface.
 */

// Get CSRF token from page
function getBallotManagementCSRFToken() {
    return jQuery("[name=csrfmiddlewaretoken]").val();
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

/**
 * Add a new candidate to the ballot.
 * @param {string} candidateName - The name of the new candidate
 * @param {string} meetingId - The meeting ID
 * @param {string} voteId - The vote/ballot ID
 * @param {function} onSuccess - Callback function on successful addition
 */
function add_candidate_ajax(candidateName, meetingId, voteId, onSuccess) {
    var csrftoken = getBallotManagementCSRFToken();

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    $.ajax({
        type: 'POST',
        url: '/api/manage/' + meetingId + '/' + voteId + '/add_option',
        data: {
            'name': candidateName
        },
        dataType: 'json',
        success: function (data) {
            if (data.result === "success") {
                if (onSuccess) {
                    onSuccess(data);
                }
            }
        },
        error: function(xhr, status, error) {
            console.error("Error adding candidate:", error);
        }
    });
}

/**
 * Remove a candidate from the ballot.
 * @param {number} candidateId - The ID of the candidate to remove
 * @param {string} meetingId - The meeting ID
 * @param {string} voteId - The vote/ballot ID
 * @param {function} onSuccess - Callback function on successful removal
 */
function remove_candidate_ajax(candidateId, meetingId, voteId, onSuccess) {
    var csrftoken = getBallotManagementCSRFToken();

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    $.ajax({
        type: 'POST',
        url: '/api/manage/' + meetingId + '/' + voteId + '/remove_option',
        data: {
            'id': candidateId
        },
        dataType: 'json',
        success: function (data) {
            if (data.result === "success") {
                if (onSuccess) {
                    onSuccess(data);
                }
            } else if (data.reason === "cannot_remove_none_of_the_above") {
                console.warn("Cannot remove 'None of the above' option");
            }
        },
        error: function(xhr, status, error) {
            console.error("Error removing candidate:", error);
        }
    });
}
