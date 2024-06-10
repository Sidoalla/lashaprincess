document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    var selectedDate = null;
    var selectedTime = null;
    var userName = null;
    var userEmail = null;
    var tooltip = document.getElementById('tooltip');
    var clickTimeout = null;
    var doubleClick = false;

    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        initialDate: new Date(),
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,dayGridWeek,dayGridDay'
        },
        events: '/get_events/',
        dateClick: function(info) {
            if (clickTimeout) {
                clearTimeout(clickTimeout);
                clickTimeout = null;
                doubleClick = true;
                handleDateDoubleClick(info);
            } else {
                clickTimeout = setTimeout(function() {
                    if (!doubleClick) {
                        handleDateClick(info);
                    }
                    doubleClick = false;
                    clickTimeout = null;
                }, 300);
            }
        },
        eventMouseEnter: function(info) {
            var event = info.event;
            var tooltipContent = `
                <div><strong>${event.title}</strong></div>
                <div>${event.start.toLocaleString()}</div>
            `;
            tooltip.innerHTML = tooltipContent;
            tooltip.style.display = 'block';
            tooltip.style.top = (info.jsEvent.pageY + 10) + 'px';
            tooltip.style.left = (info.jsEvent.pageX + 10) + 'px';
        },
        eventMouseLeave: function(info) {
            tooltip.style.display = 'none';
        },
        editable: true,
        eventClick: function(info) {
            if (clickTimeout) {
                clearTimeout(clickTimeout);
                clickTimeout = null;
                doubleClick = true;
                handleEventDoubleClick(info);
            } else {
                clickTimeout = setTimeout(function() {
                    if (!doubleClick) {
                        handleEventClick(info);
                    }
                    doubleClick = false;
                    clickTimeout = null;
                }, 300);
            }
        },
        eventDrop: function(info) {
            handleEventDrop(info);
        }
    });
    calendar.render();

    function handleDateClick(info) {
        selectedDate = info.dateStr;
        fetch(`/get_events/?date=${selectedDate}`)
            .then(response => response.json())
            .then(data => {
                if (data.length >= 3) {
                    alert('Numero massimo di prenotazioni raggiunto per questo giorno.');
                } else {
                    document.getElementById('modal-overlay').style.display = 'block';
                    document.getElementById('time-selection-modal').style.display = 'block';
                    generateTimeOptions(data);
                }
            });
    }

    function handleDateDoubleClick(info) {
        fetch('/is_admin/')
            .then(response => response.json())
            .then(data => {
                if (data.is_admin) {
                    // Aggiungi effetto di tremolio agli eventi del giorno
                    var events = calendar.getEvents();
                    events.forEach(function(event) {
                        if (event.startStr === info.dateStr) {
                            event.setProp('classNames', ['shake']);
                        }
                    });
                    setTimeout(function() {
                        events.forEach(function(event) {
                            if (event.startStr === info.dateStr) {
                                event.setProp('classNames', []);
                            }
                        });
                    }, 2000); // Durata dell'effetto di tremolio
                } else {
                    document.getElementById('login-modal').style.display = 'block';
                }
            });
    }

    function handleEventClick(info) {
        var event = info.event;
        var tooltipContent = `
            <div><strong>${event.title}</strong></div>
            <div>${event.start.toLocaleString()}</div>
        `;
        tooltip.innerHTML = tooltipContent;
        tooltip.style.display = 'block';
        tooltip.style.top = (info.jsEvent.pageY + 10) + 'px';
        tooltip.style.left = (info.jsEvent.pageX + 10) + 'px';
    }

    function handleEventDoubleClick(info) {
        fetch('/is_admin/')
            .then(response => response.json())
            .then(data => {
                if (data.is_admin) {
                    var confirmed = confirm('Vuoi modificare o cancellare questa prenotazione?');
                    if (confirmed) {
                        openEditModal(info.event);
                    }
                } else {
                    document.getElementById('login-modal').style.display = 'block';
                }
            });
    }

    function handleEventDrop(info) {
        fetch('/is_admin/')
            .then(response => response.json())
            .then(data => {
                if (data.is_admin) {
                    var confirmed = confirm('Vuoi spostare questa prenotazione?');
                    if (confirmed) {
                        updateEvent(info.event);
                    } else {
                        info.revert();
                    }
                } else {
                    alert('Non hai i permessi per modificare o cancellare questa prenotazione.');
                    info.revert();
                }
            });
    }

    function openEditModal(event) {
        var modal = document.getElementById('edit-modal');
        var eventId = event.id;
        modal.querySelector('#event-id').value = eventId;
        modal.querySelector('#event-title').innerText = event.title;
        modal.querySelector('#event-start').innerText = event.start.toISOString();
        modal.querySelector('#event-end').innerText = event.end ? event.end.toISOString() : '';
        modal.style.display = 'block';
    }

    function closeEditModal() {
        var modal = document.getElementById('edit-modal');
        modal.style.display = 'none';
    }

    function updateEvent(event) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/modifica_prenotazione/' + event.id + '/', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function() {
            if (xhr.status === 200) {
                alert('Prenotazione aggiornata con successo.');
            } else {
                alert('Errore durante l\'aggiornamento della prenotazione.');
            }
        };
        xhr.send(JSON.stringify({
            data_prenotazione: event.start.toISOString().split('T')[0],
            ora_prenotazione: event.start.toISOString().split('T')[1].substring(0, 5)
        }));
    }

    function generateTimeOptions(events) {
        var ul = document.getElementById('time-list');
        ul.innerHTML = '';
        var startTime = 9.5;
        var endTime = 18.5;
        var allTimes = [];
        for (var hour = startTime; hour <= endTime; hour += 0.5) {
            var hourPart = Math.floor(hour);
            var minutePart = (hour % 1) * 60;
            var label = ('0' + hourPart).slice(-2) + ':' + ('0' + minutePart).slice(-2);
            allTimes.push(label);
        }

        var bookedTimes = events.map(event => {
            var date = new Date(event.start);
            return date.getHours() + date.getMinutes() / 60;
        });

        allTimes.forEach(time => {
            var isAvailable = bookedTimes.every(bookedTime => {
                var selectedHour = parseInt(time.split(':')[0]);
                var selectedMinute = parseInt(time.split(':')[1]);
                var selectedTimeInHours = selectedHour + selectedMinute / 60;

                return bookedTimes.every(bookedTime => {
                    var timeDiff = Math.abs(selectedTimeInHours - bookedTime);
                    return timeDiff >= 3;
                });
            });

            var li = document.createElement('li');
            li.classList.add('list-group-item', 'list-group-item-action');
            if (!isAvailable) {
                li.classList.add('unavailable');
                li.onclick = function() {
                    alert('L\'orario selezionato è già prenotato o troppo vicino a un altro appuntamento. Scegli un altro orario.');
                };
            } else {
                li.onclick = function() {
                    var siblings = ul.children;
                    for (var i = 0; i < siblings.length; i++) {
                        siblings[i].classList.remove('active');
                    }
                    this.classList.add('active');
                    selectedTime = this.textContent;
                    showSummaryModal();
                };
            }
            li.textContent = time;
            ul.appendChild(li);
        });
    }

    function showSummaryModal() {
        userName = prompt("Inserisci il tuo nome:");
        userEmail = prompt("Inserisci la tua email:");
        if (userName && userEmail) {
            var summary = `Nome: ${userName}<br>Email: ${userEmail}<br>Data: ${selectedDate}<br>Ora: ${selectedTime}`;
            document.getElementById('summary-content').innerHTML = summary;
            document.getElementById('modal-overlay').style.display = 'none';
            document.getElementById('time-selection-modal').style.display = 'none';
            document.getElementById('summary-modal-overlay').style.display = 'block';
            document.getElementById('summary-modal').style.display = 'block';
        } else {
            closeModal();
        }
    }

    function closeSummaryModal() {
        document.getElementById('summary-modal-overlay').style.display = 'none';
        document.getElementById('summary-modal').style.display = 'none';
        closeModal();
    }

    function confirmBooking() {
        var emailConsent = document.getElementById('email-consent').checked;

        if (userName && userEmail && selectedDate && selectedTime) {
            fetch('/aggiungi_prenotazione/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    nome: userName,
                    email: userEmail,
                    data_prenotazione: selectedDate,
                    ora_prenotazione: selectedTime,
                    email_consent: emailConsent
                })
            }).then(response => {
                return response.json().then(data => {
                    if (response.ok) {
                        calendar.addEvent({
                            title: `Prenotazione di ${userName}`,
                            start: `${selectedDate}T${selectedTime}`,
                            allDay: false
                        });
                        closeSummaryModal();
                    } else {
                        alert(data.message || 'Errore durante la prenotazione.');
                        closeSummaryModal();
                    }
                });
            }).catch(error => {
                console.error('Error:', error);
                closeSummaryModal();
            });
        } else {
            closeSummaryModal();
        }
    }

    function closeModal() {
        document.getElementById('modal-overlay').style.display = 'none';
        document.getElementById('time-selection-modal').style.display = 'none';
        selectedTime = null;
        calendar.render();
    }

    window.closeModal = closeModal;
    window.closeSummaryModal = closeSummaryModal;
    window.confirmBooking = confirmBooking;
});
