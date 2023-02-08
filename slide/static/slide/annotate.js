let counter = 0;
let g_lastBoundingBoxStartX = -1;
let g_lastBoundingBoxStartY = -1;
let g_lastElementId = null;


/*
    POINTER ANNOTATIONS
 */
function activatePointerAnnotation() {
    console.log('Activating Pointer annotation');

    deactivateAnnotationMode();

    $('#pointer-annotation-btn').addClass('active');
    $('#annotation-instructions').text(
        'Double click the canvas where you want to make a pointer'
    );
    addPointerHandlers();
}

function addPointer(viewportPoint, text) {
   // Create overlay
   let textDiv = document.createElement("div");
   textDiv.className = "overlay";
   let strCounter = counter.toString();
   textDiv.id = "pointer-" + strCounter;
   textDiv.innerHTML = '<a>X</a> ' +
       '<input type="hidden" name="pointer-' + strCounter + '-x" value="' + viewportPoint.x.toString() + '"> ' +
       '<input type="hidden" name="pointer-' + strCounter + '-y" value="' + viewportPoint.y.toString() + '"> ' +
       '<input type="text" name="pointer-' + strCounter + '-text" value="' + text + '"> &#8594;';
   counter += 1;

   viewer.addOverlay(textDiv, viewportPoint, OpenSeadragon.Placement.RIGHT);

    // MouseTracker is required for links to function in overlays
    let asd = new OpenSeadragon.MouseTracker({
        element: textDiv.id,
        clickHandler: function(event) {
            let target = event.originalEvent.target;
            if(target.matches('input')) {
                target.focus();
            } else if(target.matches('a')) {
                // Event handler for deleting:
                viewer.removeOverlay(textDiv.id);
            }
        }
    });

    deactivateAnnotationMode();
    return textDiv;
}

/*
    POINTER EVENT HANDLERS
 */
function onDoubleClickPointer(event) {
    let webPoint = event.position;
    let viewportPoint = viewer.viewport.pointFromPixel(webPoint);

    let textDiv = addPointer(viewportPoint, '');
    $("#" + textDiv.id + " input[type=text]").focus();
}

function addPointerHandlers() {
    viewer.addHandler('canvas-double-click', onDoubleClickPointer);
}

function removePointerHandlers() {
    viewer.removeHandler('canvas-double-click', onDoubleClickPointer);
}

/*
    BOUNDING BOX ANNOTATIONS
 */
function activateBoxAnnotation() {
    console.log('Activating BoundingBox annotation. counter = ', counter);

    deactivateAnnotationMode();
    disablePanAndZoom();

    $('#box-annotation-btn').addClass('active');
    $('#annotation-instructions').text(
        'Click and drag to make a bounding box'
    );
    addBoundingBoxHandlers();
}

function addBoundingBox(x1, y1, x2, y2, text='') {
    console.log("In function addBoundingBox()");

    let divElement = document.createElement('div');
    viewer.addOverlay(divElement);
    divElement.id = 'boundingbox-' + counter.toString();
    drawBoundingBox(divElement.id, x1, y1, x2, y2, text);

    // MouseTracker is required for links to function in overlays
    let tracker = mouseTrackerRemoveBoundingBox(divElement);

    counter += 1;
    return divElement.id;
}

function newBoundingBox(x1, y1, x2, y2, text='') {
    console.log("In function newBoundingBox()");

    let lastBoundingBox = document.getElementById(g_lastElementId);
    //viewer.removeOverlay(lastBoundingBox);

    let divElement = document.createElement('div');
    viewer.addOverlay(divElement);
    divElement.id = 'boundingbox-' + counter.toString();
    console.log(divElement.id);

    // TODO: Must we draw the box again??
    drawBoundingBox(divElement.id, x1, y1, x2, y2, text);

    // MouseTracker is required for links to function in overlays
    let tracker = mouseTrackerRemoveBoundingBox(divElement);

    counter += 1;
    return divElement.id;
}

function drawBoundingBox(elementId, x1, y1, x2, y2, text='') {

    let tempElement = document.getElementById(elementId);
    //let tempElement = document.createElement('div');

    let x0 = Math.min(x1, x2);
    let y0 = Math.min(y1, y2);
    let width = Math.abs(x1-x2);
    let height = Math.abs(y1-y2);

    tempElement.className = 'overlay card LPBoundingBox';

    viewer.removeOverlay(tempElement);
    viewer.addOverlay({     //box, startPoint, OpenSeadragon.Placement.BOTTOM_RIGHT);
        element: tempElement,
        location: new OpenSeadragon.Rect(x0, y0, width, height)
    });
    tempElement.innerHTML = boundingBoxInnerHTML(x1, y1, x2, y2, text);

    console.log('Drew bounding box nr ' + counter);
    return tempElement;
}

function boundingBoxInnerHTML(x1, y1, x2, y2, text='') {
    let x0 = Math.min(x1, x2);
    let y0 = Math.min(y1, y2);
    let width = Math.abs(x1-x2);
    let height = Math.abs(y1-y2);
    return '<div class="row" style="margin: 0;">' +
        '<div class="col" style="padding: 0; margin-right: auto;">' +
        '   <input type="text" name="boundingbox-' + counter + '-text" value="' + text + '">' +
        '</div>' +
        '<div class="col-2" style="padding: 0;">' +
        '   <div class="LPButton removeBoundingBox" style="padding: 5px; width: 30px; height: 30px; text-align: center;">' +
        '       <a>X</a>' +
        '   </div> ' +
        '</div>' +
        '</div>' +
        '<input type="hidden" name="boundingbox-' + counter + '-x" value="' + x0.toString() + '">' +
        '<input type="hidden" name="boundingbox-' + counter + '-y" value="' + y0.toString() + '">' +
        '<input type="hidden" name="boundingbox-' + counter + '-width" value="' + width.toString() + '">' +
        '<input type="hidden" name="boundingbox-' + counter + '-height" value="' + height.toString() + '">'
}

function mouseTrackerRemoveBoundingBox(divElement) {
    return new OpenSeadragon.MouseTracker({
        element: divElement.id,
        clickHandler: function (event) {
            let target = event.originalEvent.target;
            if (target.matches('input')) {
                target.focus();
            } else if (target.matches('.removeBoundingBox')) {
                // Event handler for deleting:
                viewer.removeOverlay(divElement.id);
            } else if (target.matches('a')) {
                // Event handler for deleting:
                viewer.removeOverlay(divElement.id);
            }
        }
    });
}

/*
    BOUNDING BOX EVENT HANDLERS
 */
function onPressBoundingBox(event) {
    let webPoint = event.position;
    let startViewportPoint = viewer.viewport.pointFromPixel(webPoint);
    g_lastBoundingBoxStartX = startViewportPoint.x;
    g_lastBoundingBoxStartY = startViewportPoint.y;

    console.log('Canvas press at (' + g_lastBoundingBoxStartX.toString() + ', ' + g_lastBoundingBoxStartY.toString() + ')');
}

function onDragBoundingBox(event) {
    let webPoint = event.position;
    let viewportPoint = viewer.viewport.pointFromPixel(webPoint);

    // Create bounding box start point
    drawBoundingBox(
        g_lastElementId,
        g_lastBoundingBoxStartX, g_lastBoundingBoxStartY,
        viewportPoint.x, viewportPoint.y,
        'bounding box'
    );
    // TODO: Fix Uncaught TypeError: Cannot set properties of null --> some MouseTracker error
    /*let ms_tracker = new OpenSeadragon.MouseTracker({
        element: document.getElementById(g_lastElementId),
        dragHandler: drawBoundingBox(
            g_lastElementId,
            g_lastBoundingBoxStartX, g_lastBoundingBoxStartY,
            viewportPoint.x, viewportPoint.y,
            'bounding box'
        )
    });*/
}

function onReleaseBoundingBox(event) {
    let webPoint = event.position;
    let endViewportPoint = viewer.viewport.pointFromPixel(webPoint);
    console.log('Canvas release at (' + endViewportPoint.x.toString() + ', ' + endViewportPoint.x.toString() + ')');

    // Create bounding box
    g_lastElementId = newBoundingBox(
        g_lastBoundingBoxStartX, g_lastBoundingBoxStartY,
        endViewportPoint.x, endViewportPoint.y,
        'bounding box'
    );
    g_lastBoundingBoxStartX = -1;
    g_lastBoundingBoxStartY = -1;

    // Re-enable pan/zoom and remove canvas actions for bounding box
    deactivateAnnotationMode();
}

function addBoundingBoxHandlers() {
    viewer.addHandler('canvas-press', onPressBoundingBox);
    viewer.addHandler('canvas-drag', onDragBoundingBox);
    viewer.addHandler('canvas-release', onReleaseBoundingBox);
}

function removeBoundingBoxHandlers() {
    viewer.removeHandler('canvas-press', onPressBoundingBox);
    viewer.removeHandler('canvas-drag', onDragBoundingBox);
    viewer.removeHandler('canvas-release', onReleaseBoundingBox);
}


/*
    HELPER FUNCTIONS
 */
function disablePanAndZoom() {
    viewer.panHorizontal = false;
    viewer.panVertical = false;
    viewer.zooming = false;
    console.log('Disabled pan and zoom');
}

function enablePanAndZoom() {
    viewer.panHorizontal = true;
    viewer.panVertical = true;
    viewer.zooming = true;
    console.log('Enabled pan and zoom');
}

function deactivateAnnotationMode() {
    // Deactivate (remove highlighting) of annotation type selector buttons
    $('#pointer-annotation-btn').removeClass('active');
    $('#box-annotation-btn').removeClass('active');

    // Remove annotation handlers from canvas
    removePointerHandlers();
    removeBoundingBoxHandlers();

    enablePanAndZoom();
}
