// Global variables
let syncQueue = [];
let isSyncing = false;
let activeQuestionStartTime = Date.now();
const activeUILocks = new Set();

const SyncManager = {
    // Call this specifically inside orchestrateQuestionSwitch BEFORE switching active_question
    recordTimeOnActiveQuestion: function (old_q_id) {
        const now = Date.now();
        const timeSpentSecs = Math.floor((now - activeQuestionStartTime) / 1000);

        if (timeSpentSecs > 0) {
            syncQueue.push(["time_sync_q", old_q_id, timeSpentSecs]);
        }
        console.log("Time spent seconds on previous question: ", timeSpentSecs);

        activeQuestionStartTime = now; // Reset timer for the new question
    }
};

const StateManager = {
    update: function (pathArray, value) {
        // Write to local state
        let current = data.session_recording;
        for (let i = 0; i < pathArray.length - 1; i++) {
            current = current[pathArray[i]];
        }
        // set the last nodes value
        current[pathArray[pathArray.length - 1]] = value;

        // Push to queue in minimal format
        syncQueue.push([pathArray, value]);
    }
};

function beginHeartBeat() {
    syncQueue.push(["hb"]);
    setInterval(() => {
        syncQueue.push(["hb"]);
    }, 20000);
}

function initiateSyncQueueProcessor() {
    setInterval(async () => {
        // SUPER IMPORTANT - IF REMOVED MULIPLE WORKER QUEUES WILL START WORKING BECUASE NESTED SETINTERVAL AND SETTIMEOUT
        if (syncQueue.length === 0 || isSyncing) return;

        isSyncing = true;

        // Copy queue and clear original
        const batch = [...syncQueue];
        syncQueue = [];

        try {
            const response = await fetch('/api/exam_interface/sync/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(batch)
            });

            if (response.ok) {
                // Unlock UI on success
                unLockUI(UILockReason["SYNC_ERROR"])

                isSyncing = false;
            } else {

                const data = await response.json()

                if (data.error == "exam_ended") {
                    window.location.assign("/")
                }
                throw new Error("Server rejected batch");
            }
        } catch (error) {
            // lock the ui and keep it locked until we get a success response if we fail
            lockUI(UILockReason["SYNC_ERROR"])

            console.error("Sync failed, re-queueing:", error);

            // Put failed operations back at the front of the queue to preserve chronological order
            syncQueue = [...batch, ...syncQueue];

            // Leave UI locked if server didn't respond 200
            // Add a slight delay before allowing the worker to try the same batch again.
            setTimeout(() => { isSyncing = false; }, 2000);
        }
    }, 1000); // process queue every 1 sec
}


const maxStringSizedForPill = 24
const maxStringSizedForToolTip = 28
const QuestionSwitchReason = Object.freeze({
    SECTION_CHANGE: "SECTION_CHANGE",
    SAVE_AND_NEXT_BUTTON: "SAVE_AND_NEXT_BUTTON",
    MARK_FOR_REVIEW_BUTTON: "MARK_FOR_REVIEW_BUTTON",
    PREVIOUS_BUTTON: "PREVIOUS_BUTTON",
    SIDE_PANEL_NAVIGATION: "SIDE_PANEL_NAVIGATION",
    CLEAR_RESPONSE_BUTTON: "CLEAR_RESPONSE_BUTTON"
});
const UILockReason = Object.freeze({
    SYNC_ERROR: "SYNC_ERROR",
    QUESTION_SWITCH: "QUESTION_SWITCH",
    BEHAVIOR_DELAY: "BEHAVIOR_DELAY",
    SUBMIT_EXAM: "SUBMIT_EXAM",
});


const SIDE_PANEL_STATUS_CLASS = {
    answered: "answered",
    answered_and_marked_for_review: "review_answered",
    not_answered: "not_answered",
    not_visited: "not_visited",
    marked_for_review: "review"
}

const QuestionTypeShortForm = { "Multiple Choice": "MCQ", "Multiple Select": "MSQ", "Numerical": "NAT" }

// Helpers
function elipsizeString(str, maxLength) {
    if (str.length > maxLength) {
        return str.slice(0, maxLength - 3) + "..."
    }
    return str
}
function typesetMathJaxOnQuestionHtml() {
    if (!window.MathJax) return;

    const target = document.querySelector('#question-html');
    if (!target) return;

    if (MathJax.typesetClear) {
        MathJax.typesetClear([target]);
    }
    if (MathJax.typesetPromise) {
        MathJax.typesetPromise([target]).catch((err) => {
            console.error('MathJax typesetting failed:', err.message);
        });
    }
}
function unExpectedEvent(err_code) {
    alert("Critical Error: " + err_code + "\nCheck Console")
    throw new Error(err_code);

}
function getCurrentQuestionAnswer() {
    const $holder = $('#current-question-response-holder');

    if ($holder.find('input[type="radio"]:checked').length > 0) {
        return $holder.find('input[type="radio"]:checked').val();

    } else if ($holder.find('input[type="checkbox"]:checked').length > 0) {
        return $holder.find('input[type="checkbox"]:checked').map(function () {
            return $(this).val();
        }).get();


    } else if ($holder.find('input[type="text"]').length > 0) {
        return $holder.find('input[type="text"]').val();
    }

    return null;
}
function recomputeAggregates() {
    const examAggregate = {
        answered: 0,
        not_answered: 0,
        not_visited: 0,
        marked_for_review: 0,
        answered_and_marked_for_review: 0
    };

    const sections = data.session_recording.sections;
    const sectionAggregates = data.session_recording.section_aggregates;

    sections.forEach((section, index) => {
        // Preserve existing section name or default it
        const sectionName = sectionAggregates[index] ? sectionAggregates[index].section_name : `Section ${index + 1}`;

        const sectionAgg = {
            section_name: sectionName,
            answered: 0,
            not_answered: 0,
            not_visited: 0,
            marked_for_review: 0,
            answered_and_marked_for_review: 0
        };

        section.questions.forEach(question => {
            const status = question.status;

            // Increment section and exam counters if the status is valid
            if (sectionAgg.hasOwnProperty(status)) {
                sectionAgg[status]++;
                examAggregate[status]++;
            }
        });

        // Overwrite 
        sectionAggregates[index] = sectionAgg;
    });

    // Overwrite the exam aggregate with new totals
    data.session_recording.exam_aggregate = examAggregate;
}
function getPenaltyMarksInFraction(penalty) {
    if (penalty == 0.3333) {
        return "1/3"
    }
    else if (penalty == 0.6666) {
        return "2/3"
    }
    else {
        return penalty
    }
}
function toggleArrows(questionContainer) {
    const canScroll = questionContainer.scrollHeight > questionContainer.clientHeight;

    if (canScroll) {
        $("#question-container-scroll-up").show()
        $("#question-container-scroll-down").show()
    }
    else {
        $("#question-container-scroll-up").hide()
        $("#question-container-scroll-down").hide()
    }
}
function setUpTimer(data) {

    setInterval(() => {
        updateCountdown(data)
    }, 1000);

}
function getCurrentIndexSection() {
    const current_section_index = data.session_recording.current_section_index
    return { section_index: current_section_index, section: data.session_recording.sections[current_section_index] }
}
const getQuestionIndexById = (section, id) => section.questions.findIndex((q) => q.q_id == id);
function getActiveQuestion(section) {
    const active_question_index = getQuestionIndexById(section, section.active_question)
    return section.questions[active_question_index]
}
function lockUI(reason) {
    activeUILocks.add(UILockReason[reason]);
    $('#ui-block-overlay').show();
    $("#question-html").hide();
    $("#question-response-area").hide();
    $(".question_area").hide();
}
function unLockUI(reason) {
    activeUILocks.delete(UILockReason[reason]);

    // Only remove the overlay if EVERY reason for locking has been resolved
    if (activeUILocks.size === 0) {
        $('#ui-block-overlay').hide();
        $("#question-html").show();
        $("#question-response-area").show();
        $(".question_area").show();
    }
}
function setupScrollArrowListeners() {
    const questionContainer = document.getElementsByClassName("question-holder-area")[0];

    const upArrow = $('#question-container-scroll-up');
    upArrow.on("click", () => {
        questionContainer.scrollTop = 0;
    });

    const downArrow = $('#question-container-scroll-down');
    downArrow.on("click", () => {
        questionContainer.scrollTop = questionContainer.scrollHeight;
    });

    // Set up event listeners
    // resize observer and not the resize event - because resize is for viewport change only not content change
    const resizeObserver = new ResizeObserver(() => {
        // this will automatically trigger whenever the content changes
        // the window resizes, or MathJax finishes formatting.
        toggleArrows(questionContainer);
    });

    resizeObserver.observe(questionContainer);
}

// Interface setup functions
function setupCandidateDetails(data) {
    $('#candidate-name').text(data.candidate_name);

    $('#candidate-image').attr("src", data.candidate_profile_image_full_link);
    mockVar = ""
    const textLines = [
        data.candidate_name,
        data.registration_number,
    ];

    const tspans = textLines.map((line, i) =>
        `<tspan x="10" dy="${i === 0 ? 0 : 20}">${line}</tspan>`
    ).join('');

    const svg = `
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
                
            <text x="80" y="50"
                    transform="rotate(-30 150 100)"
                    fill="rgba(0,0,0,0.08)"
                    font-size="24"
                    font-family="Arial">
                ${tspans}
            </text>
            </svg>
            `;
    $('.question-holder-area').css('background-image', `url("data:image/svg+xml,${encodeURIComponent(svg)}")`);

}

function setUpExamPill() {
    $('#exam-name').text(data.exam_title)
    $('#exam-name-pill').text(elipsizeString(data.exam_title, maxStringSizedForPill))
    $('#exam-name-pill').attr("title", data.exam_title)
    $("#subject-info-grp0").find("b").text(elipsizeString(data.exam_title, maxStringSizedForToolTip))

    updateExamTooltip()
}

function setupSections() {
    const sections = data?.session_recording?.section_aggregates || [];
    const currentIndex = data?.session_recording?.current_section_index ?? 0;

    const $sections = $("#sections");
    $sections.empty();

    sections.forEach((section, i) => {
        const isSelected = i === currentIndex ? "selectedsubject" : "";
        const sectionName = section.section_name || "";

        const html = `
            <div id="section-${i}" data-section-id=${i} class="subject-name ${isSelected}" data-section-index="${i}">
                <span class="section-title" title="${sectionName}">${sectionName}</span>

                <span class="tooltip1">
                    <div class="subject_instruction_icon1 subject_instruction_icon_section"></div>

                    <div class="subject_information_div1">
                        <div class="subject_name section-name-text" style="text-align:left">
                            ${sectionName}
                        </div>

                        <div class="notation_type_description diff_type_notation_area_inner" style="background: none;text-align: left; padding-left: 8px;">
                            <div class="notation_typeDiv">
                                <span id="section-${i}-answered" class="answered">0</span>
                                <span class="type_title secAnswered longtext-hide1" style="text-align:left">Answered</span>
                            </div>

                            <div class="notation_typeDiv">
                                <span id="section-${i}-not-answered" class="not_answered">0</span>
                                <span class="type_title secNotAnswered longtext-hide1" style="text-align:left">Not Answered</span>
                            </div>

                            <div class="notation_typeDiv">
                                <span id="section-${i}-not-visited" class="not_visited">0</span>
                                <span class="type_title secNotAttempted longtext-hide1" style="text-align:left">Not Visited</span>
                            </div>

                            <div class="notation_typeDiv">
                                <span id="section-${i}-marked-review" class="review">0</span>
                                <span class="type_title secMarkReview longtext-hide1" style="text-align:left">Marked for Review</span>
                            </div>

                            <div class="notation_typeDiv review_answer">
                                <span id="section-${i}-answered-review" class="review_answered">0</span>
                                <span class="type_title secMarkedAndAnswered longtext-hide1" style="text-align:left">
                                    Answered &amp; Marked for Review
                                    (will also be evaluated)
                                </span>
                            </div>
                        </div>
                    </div>
                </span>
            </div>
        `;

        $sections.append(html);
    });

    updateSectionToolTips();
    setUpSectionPillEventListerner();
}

function setUpSidePanel() {
    updateSidePanelAggregates()
    updateSidePanelQuestionStatusIndicatorList()
    attachSidePanelEventListeners()
}

function setUpQuestionArea() {
    updateQuestionArea()
}


// High Level OrchesTration Functions
function orchestrateSectionChange() {
    lockUI(UILockReason["QUESTION_SWITCH"])

    updateSidePanelAggregates()
    updateSidePanelQuestionStatusIndicatorList()

    updateQuestionAreaWithJitter()
}


function orchestrateQuestionSwitch(reason, new_question_index = -1) {
    // unlock will be done by the last function called below
    lockUI(UILockReason["QUESTION_SWITCH"])

    console.log("SWITCHING QUESTIONS\n Reason: ", reason, "\n index: ", new_question_index);

    const { section_index, section } = getCurrentIndexSection()
    const new_question_id = section.questions[new_question_index].q_id

    const old_question = getActiveQuestion(section)
    const old_question_id = old_question.q_id
    SyncManager.recordTimeOnActiveQuestion(old_question_id)

    if (new_question_id != section.questions[new_question_index].q_id) {
        console.log(new_question_id);
        console.log(section.questions[new_question_index]);
        console.log(section.questions.indexOf((q) => q.q_id == new_question_id))
        unExpectedEvent("SIDEPANEL:QUESTION_ORDERING_MISMATCH")
    }
    // called by side panel event listner
    if (reason == QuestionSwitchReason["SIDE_PANEL_NAVIGATION"]) {
        StateManager.update(['sections', section_index, 'active_question'], new_question_id);
    }

    // called by event listner on save and next button
    if (reason == QuestionSwitchReason["SAVE_AND_NEXT_BUTTON"]) {
        StateManager.update(['sections', section_index, 'active_question'], new_question_id);
    }

    else if (reason == QuestionSwitchReason["MARK_FOR_REVIEW_BUTTON"]) {
        StateManager.update(['sections', section_index, 'active_question'], new_question_id);
    }
    else if (reason == QuestionSwitchReason["PREVIOUS_BUTTON"]) {
        StateManager.update(['sections', section_index, 'active_question'], new_question_id);
    }


    // Decide status change for new_question: becuase if status is not_visited it should become visited
    const new_question_status = section.questions[new_question_index].status
    const new_status = (new_question_status == "not_visited") ? "not_answered" : new_question_status
    if (new_status != new_question_status) {
        // the status was changed
        StateManager.update(['sections', section_index, 'questions', new_question_index, 'status'], new_status);
    }

    recomputeAggregates()
    updateExamTooltip()
    updateSectionToolTips()
    updateSidePanelAggregates()
    updateSidePanelQuestionStatusIndicatorList()
    updateQuestionAreaWithJitter()
}

// Individual Update Functions
function updateCountdown(data) {
    const now = Date.now();
    const examStartTime = new Date(data.exam_start_time);
    const diffInS = data.duration_mins * 60 - ((now - examStartTime) / 1000);

    let time = ""
    if (diffInS <= 0) {
        time = "00:00"
        $('#examination-countdown-mins').text(time)
        $('#exam_time_up_overlay').css("display", "flex")
        submit_exam();
    }
    else {
        const minutes = Math.floor(diffInS / 60);
        const seconds = Math.floor(diffInS % 60);
        time = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
    }
    $('#examination-countdown-mins').text(time)

}

function updateExamTooltip() {
    const exam_aggregate = data.session_recording.exam_aggregate
    $("#subject-info-grp0").find("#exam-answered").find('.answered').text(exam_aggregate.answered)
    $("#subject-info-grp0").find("#exam-not-answered").find('.not_answered').text(exam_aggregate.not_answered)
    $("#subject-info-grp0").find("#exam-not-visited").find('.not_visited').text(exam_aggregate.not_visited)
    $("#subject-info-grp0").find("#exam-marked-review").find('.review').text(exam_aggregate.marked_for_review)
    $("#subject-info-grp0").find("#exam-answered-review").find('.review_answered').text(exam_aggregate.answered_and_marked_for_review)
}

function updateSectionToolTips() {
    const sections = data?.session_recording?.section_aggregates || [];
    const currentIndex = data?.session_recording?.current_section_index ?? 0;

    sections.forEach((section, i) => {
        const $section = $(`#section-${i}`);
        if (!$section.length) return;

        $section.toggleClass("selectedsubject", i === currentIndex);

        $section.find(".section-title").text(section.section_name || "");
        $section.find(".section-name-text").text(section.section_name || "");

        $section.find(".answered").text(section.answered ?? 0);
        $section.find(".not_answered").text(section.not_answered ?? 0);
        $section.find(".not_visited").text(section.not_visited ?? 0);
        $section.find(".review").text(section.marked_for_review ?? 0);
        $section.find(".review_answered").text(section.answered_and_marked_for_review ?? 0);
    });
}

function updateSidePanelAggregates() {
    const current_section_index = data.session_recording.current_section_index
    const section_aggregate = data.session_recording.section_aggregates[current_section_index]
    const section_name = section_aggregate.section_name
    $('#side-panel-section-name').text(section_name)
    $('#side-panel-section-name').attr("title", section_name)

    $('#side-panel-answered-count').text(section_aggregate.answered)
    $('#side-panel-not-answered-count').text(section_aggregate.not_answered)
    $('#side-panel-not-visited-count').text(section_aggregate.not_visited)
    $('#side-panel-marked-for-review-count').text(section_aggregate.marked_for_review)
    $('#side-panel-answered-and-marked-for-review-count').text(section_aggregate.answered_and_marked_for_review)

}

function updateSidePanelQuestionStatusIndicatorList() {
    function renderSidePanelIndicator(q, index) {
        const statusClass = SIDE_PANEL_STATUS_CLASS[q.status] || "not_visited"
        const classes = [
            "tipIcon",
            "numpan",
            "sp-indicator",
            statusClass
        ].join(" ")

        return `
        <span
            id="sp-q-indicator-${q.q_id}"
            class="${classes}"
            data-q-id="${q.q_id}"
            >
            ${index + 1}
        </span>
    `
    }

    const current_section_index = data.session_recording.current_section_index
    const section_questions = data.session_recording.sections[current_section_index].questions

    const sidePanelListHtml = section_questions.map(renderSidePanelIndicator).join("")

    $('.question_area').html(sidePanelListHtml)
}

function updateQuestionAreaWithJitter() {
    if (!data.interface_behavior.question_change_delay) {
        updateQuestionArea()
        unLockUI(UILockReason["QUESTION_SWITCH"])
        return;
    }
    const fixed_delay = data.interface_behavior.question_change_delay[0]
    const plus_minus_delay = data.interface_behavior.question_change_delay[1]
    const randomOffset = (Math.random() * 2 - 1) * plus_minus_delay;

    const timeout = fixed_delay + randomOffset

    setTimeout(() => {
        updateQuestionArea()
        unLockUI(UILockReason["QUESTION_SWITCH"])
    }, timeout);
}

function updateQuestionArea() {
    const { section_index, section } = getCurrentIndexSection()

    const current_question = getActiveQuestion(section)
    const index = getQuestionIndexById(section, current_question.q_id)

    $('#current_question_type').text(current_question.q_type)
    $('#current-question-number').text(index + 1)
    $('#current-question-correct-marks').text(current_question.marks_award)
    $('#current-question-penalty-marks').text(getPenaltyMarksInFraction(current_question.marks_penalty))

    $('#question-html').html(current_question.question_html)
    typesetMathJaxOnQuestionHtml()

    renderAnswerArea(current_question.q_type)
}

function renderAnswerArea(question_type) {
    const $holder = $('<span id="current-question-response-holder" style="display:flex;margin-top:50px"></span>');
    const options = ['A', 'B', 'C', 'D'];

    const { section } = getCurrentIndexSection();
    const saved_answer = getActiveQuestion(section).user_ans;

    if (question_type === 'MCQ') {
        options.forEach(opt => {
            const isChecked = (typeof (saved_answer) == 'string' && saved_answer == opt) ? 'checked' : '';
            $holder.append(`<label><input type="radio" name="answer_input" value="${opt}" ${isChecked}> ${opt}</label>`);
        });
    } else if (question_type === 'MSQ') {
        options.forEach(opt => {
            const isChecked = (Array.isArray(saved_answer) && saved_answer.includes(opt)) ? 'checked' : '';
            $holder.append(`<label><input type="checkbox" name="answer_input" value="${opt}" ${isChecked}> ${opt}</label>`);
        });
    } else if (question_type === 'NAT') {
        const nat_value = (typeof saved_answer === 'string') ? saved_answer : '';
        $holder.append(`
            <script>triggerKeyboard(1, true)</script>
                <div style="padding-left: 4%;" id="numericKeyBoardDiv"><span id="ariaDescForSAinput"></span>
                    <input aria-labelledby="ariaDescForSAinput" type="text" id="answer" autocomplete="off"
                        class=" keyboardInput answer" readonly value="${nat_value}" onchange="checkSAMandatory(false)"
                        style="text-align: left;">
                </div>
            `);
    } else {
        console.error("Invalid question_type provided.");
        return;
    }

    $('#question-response-area').html($holder);
}
function confirm_submit_exam() {

    const section_aggregates = data.session_recording.section_aggregates
    const exam_aggregate = data.session_recording.exam_aggregate

    let total_questions = 0
    let summary_table_body = ""
    for (let i = 0; i < section_aggregates.length; i++) {
        const section = section_aggregates[i]
        const questions = data.session_recording.sections[i].questions.length
        total_questions += questions
        summary_table_body += `
            <tr>
                    <td>${section.section_name}</td>
                    <td>${data.session_recording.sections[i].questions.length}</td>
                    <td>${section.answered}</td>
                    <td>${section.not_answered}</td>
                    <td>${section.marked_for_review}</td>
                    <td>${section.answered_and_marked_for_review}</td>
                    <td>${section.not_visited}</td>
            </tr>
        `
    }
    summary_table_body += `
        <tr>
            <td style="font-weight:bold">Total</td>
            <td style="font-weight:bold">${total_questions}</td>
            <td style="font-weight:bold">${exam_aggregate.answered}</td>
            <td style="font-weight:bold">${exam_aggregate.not_answered}</td>
            <td style="font-weight:bold">${exam_aggregate.marked_for_review}</td>
            <td style="font-weight:bold">${exam_aggregate.answered_and_marked_for_review}</td>
            <td style="font-weight:bold">${exam_aggregate.not_visited}</td>
        </tr>
    `
    $('#exam_summary tbody').html(summary_table_body)

    $(".collapsebel_panel").hide();
    $(".expand_icon").hide();
    $(".collapse_icon").hide();
    $("#confirm_exam_submit_overlay").css("display", "flex");


}
function submit_exam() {
    lockUI(UILockReason["SUBMIT_EXAM"])
    async function attemptSubmitExam() {
        try {
            const response = await fetch("/api/exam_interface/submit/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
            });
            const data = await response.json()
            window.location.assign("/gate/feedback/")
        }
        catch {
        }
    }
    setTimeout(() => {
        attemptSubmitExam();
    }, 1500);
}

// Event Listner Attachers
function setUpSectionPillEventListerner() {
    // actual event listener
    $("#sections").on("click", ".subject-name", function () {
        const $clicked = $(this);

        $(".subject-name").removeClass("selectedsubject");

        $clicked.addClass("selectedsubject");

        const index = parseInt($clicked.attr("data-section-id"), 10);

        if (!isNaN(index)) {
            StateManager.update(["current_section_index"], index)
        }

        orchestrateSectionChange()
    });
}

function attachSidePanelEventListeners() {

    $('.question_area').on('click', '.sp-indicator', function (event) {
        // 'this' refers to the specific .sp-indicator that was clicked
        const { section_index, section } = getCurrentIndexSection()

        const question_id = this.attributes["data-q-id"].value
        if (question_id == section.active_question) {
            return;
        }
        const new_question_index = this.innerText - 1

        orchestrateQuestionSwitch(QuestionSwitchReason["SIDE_PANEL_NAVIGATION"], new_question_index)

    });
}

function addExamControlButtonsEventListener() {

    // save and next
    $('#save_and_next').on('click', () => {
        const { section_index, section } = getCurrentIndexSection()
        const answer = getCurrentQuestionAnswer()
        const question = getActiveQuestion(section)
        const old_status = question.status
        const old_question_id = question.q_id
        const old_question_index = getQuestionIndexById(section, old_question_id)

        let new_status = old_status
        if (answer) {
            new_status = "answered"
            StateManager.update(['sections', section_index, "questions", old_question_index, "user_ans"], answer)
        }

        if (new_status != old_status) {
            StateManager.update(['sections', section_index, "questions", old_question_index, "status"], new_status)
        }

        const new_question_index = (old_question_index + 1) % (section.questions.length)
        orchestrateQuestionSwitch(QuestionSwitchReason["SAVE_AND_NEXT_BUTTON"], new_question_index)

    });

    // mark for review
    $('#mark_for_review').on('click', () => {
        const { section_index, section } = getCurrentIndexSection()
        // dom answer
        const answer = getCurrentQuestionAnswer()
        const question = getActiveQuestion(section)
        const old_status = question.status
        const old_question_id = question.q_id
        const old_question_index = getQuestionIndexById(section, old_question_id)

        let new_status = old_status
        if (answer) {
            new_status = 'answered_and_marked_for_review'
            StateManager.update(['sections', section_index, "questions", old_question_index, "user_ans"], answer)
        }
        else {
            new_status = 'marked_for_review'
        }
        if (new_status != old_status) {
            StateManager.update(['sections', section_index, "questions", old_question_index, "status"], new_status)
        }

        const new_question_index = (old_question_index + 1) % (section.questions.length)
        orchestrateQuestionSwitch(QuestionSwitchReason["MARK_FOR_REVIEW_BUTTON"], new_question_index)

    });

    $('#previous').on('click', () => {
        const { section_index, section } = getCurrentIndexSection()
        const question = getActiveQuestion(section)
        const old_question_index = getQuestionIndexById(section, question.q_id)


        let new_question_index = 0;
        if (old_question_index == 0) {
            new_question_index = section.questions.length - 1
        }
        else {
            new_question_index = old_question_index - 1
        }
        orchestrateQuestionSwitch(QuestionSwitchReason["PREVIOUS_BUTTON"], new_question_index)

    });

    $('#clear_response').on('click', () => {
        const { section_index, section } = getCurrentIndexSection()
        const question = getActiveQuestion(section)
        const old_question_index = getQuestionIndexById(section, question.q_id)

        if (question.status == "not_answered" || question.status == "marked_for_review") {
            return;
        }
        StateManager.update(['sections', section_index, "questions", old_question_index, "user_ans"], null)
        StateManager.update(['sections', section_index, "questions", old_question_index, "status"], "not_answered")

        // Dont change question but call it so it refreshes and rerenders everything including aggregates instead of custom logic
        orchestrateQuestionSwitch(QuestionSwitchReason["CLEAR_RESPONSE_BUTTON"], old_question_index)

    });
}

function examSubmitControlEventListeners() {
    $("#exam_submit_yes").on('click', () => {
        submit_exam();
    })

    $("#exam_submit_no").on('click', () => {
        $(".collapsebel_panel").show();
        $(".collapse_icon").show();
        $("#confirm_exam_submit_overlay").css("display", "none");
    });
}
function collapseableSidePanelListners() {
    // Initial state (optional: set based on current display)
    if ($('.collapsible-question-panel').css('display') === 'flex') {
        $('.expand_icon').css('display', 'none');
        $('.collapse_icon').css('display', 'inline');
    } else {
        $('.expand_icon').css('display', 'inline');
        $('.collapse_icon').css('display', 'none');
    }

    // Click handler (adjust selector to whatever should trigger toggle)
    $('.expand_icon, .collapse_icon').on('click', function () {

        let panel = $('.collapsible-question-panel');

        if (panel.css('display') === 'none') {
            // Show panel
            panel.css('display', 'flex');

            $('.expand_icon').css('display', 'none');
            $('.collapse_icon').css('display', 'inline');

        } else {
            // Hide panel
            panel.css('display', 'none');

            $('.expand_icon').css('display', 'inline');
            $('.collapse_icon').css('display', 'none');
        }

    });

}

// Interface Behavior Controls
function applyAntiCheatLocks() {
    if (false) return;

    // 1. Disable Right-Click Menu
    document.addEventListener('contextmenu', (e) => e.preventDefault());

    // 2. Intercept Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        e.preventDefault(); // all keyboard inputs neglected
        if (
            e.key === 'F12' ||
            (e.ctrlKey && e.shiftKey && e.key === 'I') || // DevTools (Windows)
            (e.ctrlKey && e.shiftKey && e.key === 'J') || // Console
            (e.ctrlKey && e.key === 'U') || // View Source
            (e.ctrlKey && e.key === 'P') || // Print
            (e.ctrlKey && e.key === 'S') || // Save
            (e.ctrlKey && e.key === 'C') || // Copy
            (e.metaKey) // Blocks Mac Cmd combos / Windows key
        ) {
            e.preventDefault();
            return false;
        }

        // 3. Strict NAT Input validation
        if (document.activeElement.tagName === 'INPUT' && document.activeElement.type === 'text') {
            const isNumeric = (e.key >= '0' && e.key <= '9') || e.key === '.' || e.key === '-';
            const isControl = ['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(e.key);

            // Allow Ctrl+A / Ctrl+V if you want, but strictly in exam you can only use the virtual keyboard.
            if (!isNumeric && !isControl) {
                e.preventDefault();
            }
        }
    });
}
function examInterfaceBehaviorEnforcement() {
    // 1. Mouse Scroll Disable
    if (data?.interface_behavior?.mouse_scrolling === false) {
        window.addEventListener('wheel', (e) => {
            e.preventDefault();
        }, { passive: false });
    }

    if (data?.interface_behavior?.allow_early_submit) {
        $('#finalSubmit').removeAttr("disabled")
        $('#finalSubmit').on("click", () => {
            confirm_submit_exam();
        });
    }

}

function setUpExamDetails(data) {
    window.data = data

    recomputeAggregates()
    setUpExamPill()
    setupSections()

    collapseableSidePanelListners()
    addExamControlButtonsEventListener()
    setupScrollArrowListeners()
    examSubmitControlEventListeners()

    setUpSidePanel()
    setUpQuestionArea()

    applyAntiCheatLocks()
    examInterfaceBehaviorEnforcement()

    setUpTimer(data)
    beginHeartBeat()
    initiateSyncQueueProcessor()
    $('#ui-block-overlay').hide()

}

document.addEventListener('DOMContentLoaded', async () => {
    const data = await examContextHandler()

    setupCandidateDetails(data);
    setUpExamDetails(data);
});