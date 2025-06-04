document.addEventListener('DOMContentLoaded', function() {
    let draggedElement = null;
    let currentDropZone = null;
    let isOperationInProgress = false; // Flag to prevent concurrent operations

    const dndPopup = document.getElementById('dndConfirmationPopup');
    const btnMove = document.getElementById('dndConfirmMove');
    const btnCopy = document.getElementById('dndConfirmCopy');
    const btnCancel = document.getElementById('dndConfirmCancel');

    function clearDragState() {
        if (draggedElement) {
            draggedElement.style.opacity = '1';
        }
        draggedElement = null;
        currentDropZone = null;
        // Clear dataset from popup as well to prevent stale data issues
        if (dndPopup) { // Ensure dndPopup exists
            dndPopup.dataset.eventId = ''; // Clear data from popup
            dndPopup.dataset.newDate = '';
            // dndPopup.style.display = 'none'; // Hide popup if not already hidden by caller
        }
        isOperationInProgress = false; // Reset operation flag
        console.log("Drag state cleared. isOperationInProgress:", isOperationInProgress);
    }

    function addDragEventListeners(item) {
        item.addEventListener('dragstart', function(event) {
            if (isOperationInProgress) { // Prevent starting a new drag if an operation is pending (e.g. popup visible)
                event.preventDefault();
                console.log("Dragstart prevented: operation in progress.");
                return;
            }
            draggedElement = event.target; // Keep track of the currently dragged element
            event.dataTransfer.setData('text/plain', event.target.dataset.eventId);
            setTimeout(() => {
                if(draggedElement) draggedElement.style.opacity = '0.5';
            }, 0);
        });

        item.addEventListener('dragend', function(event) {
            if (dndPopup.style.display === 'none' && !isOperationInProgress) {
                clearDragState();
            }
        });
    }

    const draggableItems = document.querySelectorAll('.event-grid-item, .shift-grid-item');
    draggableItems.forEach(addDragEventListeners);

    const dropTargets = document.querySelectorAll('td[data-date]'); // More generic selector
    dropTargets.forEach(target => {
        target.addEventListener('dragover', function(event) {
            event.preventDefault();
            target.style.backgroundColor = 'rgba(0,0,0,0.1)';
        });
        target.addEventListener('dragleave', function(event) {
            target.style.backgroundColor = '';
        });
        target.addEventListener('drop', function(event) {
            event.preventDefault();
            target.style.backgroundColor = '';

            if (isOperationInProgress) {
                console.log("Drop ignored: operation already in progress.");
                // Optionally, reset draggedElement's opacity if it was made semi-transparent
                if (draggedElement) draggedElement.style.opacity = '1';
                draggedElement = null; // Clear to prevent unintended state
                return;
            }

            if (event.target === draggedElement || (draggedElement && event.target.contains(draggedElement)) || (draggedElement && event.target === draggedElement.parentElement)) {
                if (draggedElement) draggedElement.style.opacity = '1';
                draggedElement = null;
                return;
            }

            currentDropZone = event.currentTarget;
            const eventIdStr = event.dataTransfer.getData('text/plain');
            const newDateStr = currentDropZone.dataset.date;

            if (!eventIdStr || !newDateStr || !draggedElement) {
                console.error('Drop event failed: missing eventId, newDate, or draggedElement was not set.');
                clearDragState();
                return;
            }

            dndPopup.dataset.eventId = eventIdStr;
            dndPopup.dataset.newDate = newDateStr;

            dndPopup.style.left = event.pageX + 'px';
            dndPopup.style.top = event.pageY + 'px';
            dndPopup.style.display = 'block';
        });
    });

    // Event listeners for popup buttons are set only once
    btnMove.addEventListener('click', function() {
        if (isOperationInProgress) {
            console.log("Move operation already in progress.");
            return;
        }
        const eventIdStr = dndPopup.dataset.eventId;
        const newDateStr = dndPopup.dataset.newDate;

        if (!eventIdStr || !newDateStr || !draggedElement || !currentDropZone) {
            console.error('Move Pre-condition failed. EventID:', eventIdStr, 'NewDate:', newDateStr, 'DE:', draggedElement, 'CDZ:', currentDropZone);
            dndPopup.style.display = 'none';
            clearDragState();
            return;
        }

        isOperationInProgress = true;
        dndPopup.style.display = 'none';
        console.log('Move button clicked. EventID:', eventIdStr, 'NewDate:', newDateStr);
        handleDropOperation("move", parseInt(eventIdStr), newDateStr, draggedElement, currentDropZone);
    });

    btnCopy.addEventListener('click', function() {
        if (isOperationInProgress) {
            console.log("Copy operation already in progress.");
            return;
        }
        const eventIdStr = dndPopup.dataset.eventId;
        const newDateStr = dndPopup.dataset.newDate;

        if (!eventIdStr || !newDateStr || !draggedElement || !currentDropZone) {
            console.error('Copy Pre-condition failed. EventID:', eventIdStr, 'NewDate:', newDateStr, 'DE:', draggedElement, 'CDZ:', currentDropZone);
            dndPopup.style.display = 'none';
            clearDragState();
            return;
        }
        isOperationInProgress = true;
        dndPopup.style.display = 'none';
        console.log('Copy button clicked. EventID:', eventIdStr, 'NewDate:', newDateStr);
        handleDropOperation("copy", parseInt(eventIdStr), newDateStr, draggedElement, currentDropZone);
    });

    btnCancel.addEventListener('click', function() {
        console.log('Cancel button clicked. isOperationInProgress:', isOperationInProgress);
        dndPopup.style.display = 'none';
        // If an operation was technically "in progress" (e.g. popup was visible),
        // but no async action (like fetch) has started, this is fine.
        // If fetch had started, it won't be aborted by this, but UI is reset.
        clearDragState();
    });

    async function handleDropOperation(operation, eventId, newDate, elementToProcess, targetDropZone) {
        console.log(`handleDropOperation: op=${operation}, eid=${eventId}, date=${newDate}. isOperationInProgress: ${isOperationInProgress}`);
        console.log('elementToProcess:', elementToProcess);
        console.log('targetDropZone:', targetDropZone);

        // Pre-condition check, though mostly handled by callers now
        if (!elementToProcess || !targetDropZone) {
             console.error("handleDropOperation critical error: elementToProcess or targetDropZone is null.");
             clearDragState();
             return;
        }

        try {
            const response = await fetch(apiEventDropUrl, { // MODIFIED HERE
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ event_id: eventId, new_date: newDate, operation: operation })
            });
            const data = await response.json();
            console.log('API Response Status:', response.status, 'API Data:', data);

            if (!isOperationInProgress && operation !== "cancel_after_fetch_started_scenario") {
                // This check is tricky. If user cancelled *while* fetch was ongoing.
                // For now, we assume if user cancelled, clearDragState already set isOperationInProgress to false.
                // And the DOM element (elementToProcess) might be out of sync or opacity restored.
                console.log("Operation was cancelled or finished before fetch completed. Aborting DOM update.");
                // Ensure element's opacity is restored if it's still the one we were dragging
                if (elementToProcess && elementToProcess.style.opacity !== '1') {
                     // elementToProcess.style.opacity = '1'; // This is now handled by clearDragState
                }
                return; // Don't proceed with DOM updates if operation flag was reset by cancel.
            }

            if (data.success) {
                if (operation === 'move') {
                    targetDropZone.appendChild(elementToProcess);
                    // Opacity is handled by clearDragState via finally
                } else if (operation === 'copy' && data.new_event_id) {
                    const clonedElement = elementToProcess.cloneNode(true);
                    clonedElement.dataset.eventId = data.new_event_id;
                    const editLink = clonedElement.querySelector('a.btn-custom-edit');
                    // The URL for edit_event might need to be passed or constructed differently if it's complex
                    // For now, assuming a simple replacement will work, but this is a potential issue.
                    if (editLink) editLink.href = editLink.href.substring(0, editLink.href.lastIndexOf('/') + 1) + data.new_event_id;
                    const detailsButton = clonedElement.querySelector('button.details-btn');
                    if (detailsButton) detailsButton.dataset.eventId = data.new_event_id;

                    targetDropZone.appendChild(clonedElement);
                    addDragEventListeners(clonedElement);
                    clonedElement.style.opacity = '1'; // Ensure clone is visible
                } else if (operation === 'copy' && !data.new_event_id) {
                     alert('エラー: コピー操作で新しいイベントIDが取得できませんでした。');
                     location.reload(); // Fallback for this specific error
                     return; // Important to return to avoid finally block double-clearing or errors
                }
                alert(data.message || '操作が完了しました。');
            } else {
                alert('エラー: ' + (data.error || '不明なエラーが発生しました。'));
                // If API call failed, restore opacity of the original dragged element
                if (elementToProcess) elementToProcess.style.opacity = '1';
            }
        } catch (error) {
            console.error('Error in handleDropOperation:', error);
            alert('通信エラーが発生しました。');
            if (elementToProcess) elementToProcess.style.opacity = '1';
        } finally {
            console.log('handleDropOperation finally block. Clearing state.');
            clearDragState();
        }
    }

    // --- New functionality for Copy/Move buttons and Date Selection Modal ---
    const dateSelectionModal = document.getElementById('dateSelectionModal');
    const dateSelectionInput = document.getElementById('dateSelectionInput');
    const dateSelectionConfirmBtn = document.getElementById('dateSelectionConfirm');
    const dateSelectionCancelBtn = document.getElementById('dateSelectionCancel');
    const dateSelectionModalTitle = document.getElementById('dateSelectionModalTitle');

    let currentEventIdForModal = null;
    let currentOperationForModal = null;

    function showDateSelectionModal(eventId, operation) {
        console.log('[showDateSelectionModal] eventId:', eventId, 'operation:', operation); // DEBUG
        currentEventIdForModal = eventId;
        currentOperationForModal = operation;
        dateSelectionInput.value = ''; // Clear previous date
        const operationText = operation === 'copy' ? 'コピー' : '移動';
        dateSelectionModalTitle.textContent = `${operationText}先の日付を選択してください`;
        if (dateSelectionModal) { // Check if modal exists on the page
            dateSelectionModal.style.display = 'flex'; // Show modal (using flex as per existing centering styles)
            console.log('[showDateSelectionModal] Modal display set to flex'); // DEBUG
        } else {
            console.error('[showDateSelectionModal] Date selection modal not found on this page.');
        }
    }

    function hideDateSelectionModal() {
        if (dateSelectionModal) {
            dateSelectionModal.style.display = 'none'; // Hide modal
            console.log('[hideDateSelectionModal] Modal display set to none'); // DEBUG
        }
        currentEventIdForModal = null;
        currentOperationForModal = null;
    }

    document.querySelectorAll('.btn-custom-copy, .btn-custom-move').forEach(button => {
        button.addEventListener('click', function(event) {
            const eventId = this.dataset.eventId;
            const operation = this.classList.contains('btn-custom-copy') ? 'copy' : 'move';
            console.log('[Button Click] eventId:', eventId, 'operation:', operation); // DEBUG
            if (eventId) {
                showDateSelectionModal(parseInt(eventId), operation);
            } else {
                console.error('[Button Click] Event ID not found on button.');
            }
        });
    });

    if (dateSelectionConfirmBtn) {
        dateSelectionConfirmBtn.addEventListener('click', async function() {
            const newDate = dateSelectionInput.value;
            console.log('[Modal Confirm Click] newDate:', newDate, 'currentEventIdForModal:', currentEventIdForModal, 'currentOperationForModal:', currentOperationForModal); // DEBUG
            if (!newDate) {
                alert('日付を選択してください。');
                return;
            }
            if (!currentEventIdForModal || !currentOperationForModal) {
                console.error('[Modal Confirm Click] Event ID or operation type for modal is missing.');
                hideDateSelectionModal();
                return;
            }

            // Use the existing handleDropOperation logic if possible, or call API directly
            // For simplicity, directly calling API like handleDropOperation
            // This assumes 'elementToProcess' and 'targetDropZone' are not strictly needed for API
            // or that the API can handle their absence for this type of operation.

            const fetchBody = {
                event_id: currentEventIdForModal,
                new_date: newDate,
                operation: currentOperationForModal
            };
            console.log('[Modal Confirm Click] Fetching API. URL:', apiEventDropUrl, 'Body:', JSON.stringify(fetchBody)); // DEBUG

            try {
                const response = await fetch(apiEventDropUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(fetchBody)
                });
                const data = await response.json();
                console.log('[Modal Confirm Click] API Response Status:', response.status, 'API Data:', data); // DEBUG

                if (data.success) {
                    alert(data.message || `${currentOperationForModal === 'copy' ? 'コピー' : '移動'}が完了しました。`);
                    location.reload(); // Reload page on success
                } else {
                    alert('エラー: ' + (data.error || '不明なエラーが発生しました。'));
                }
            } catch (error) {
                console.error('Error in modal confirm operation:', error);
                alert('通信エラーが発生しました。');
            } finally {
                hideDateSelectionModal();
            }
        });
    }

    if (dateSelectionCancelBtn) {
        dateSelectionCancelBtn.addEventListener('click', function() {
            hideDateSelectionModal();
        });
    }
});
