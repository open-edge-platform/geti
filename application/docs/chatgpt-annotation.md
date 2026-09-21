# Annotate with ChatGPT

The Windows desktop application can send the current image to the configured
ChatGPT connection or OpenAI API connection and show proposed annotations in the
editor. It can also pre-label a representative subset of unannotated images from
the Dataset page.

## Auto-label a dataset

Choose **Auto-Label** on the Dataset page, then select one of these modes:

- **Pretrained Auto-Label** lists only pretrained model architectures compatible
  with the project's task and capable of producing semantic predictions from
  their original checkpoint. Choose a model to process every unannotated image
  and extracted video frame. Classes found by the model become project labels.
- **ChatGPT** scans all unannotated images, builds a compact overview, and asks
  ChatGPT to choose a diverse subset before generating annotations. This limits
  image and token usage while letting the model select representative samples.

Both modes save their results immediately as editable predictions that still
require review. Open an image in the annotator to edit, delete, or accept the
generated shapes. Auto-Label skips items that already have annotations, including
existing unreviewed predictions.

## Annotate an image

1. Open a dataset image in **Annotation** mode and select **Annotate with ChatGPT**.
   You can also choose this option from the dataset's **Annotate** menu; it opens
   the first image in the displayed media list.
2. If prompted, connect using the drawer's settings. Wait for the connection
   indicator and the current image thumbnail to appear.
3. Describe what to annotate, for example, “Mark every red candy.” You can also
   press **Send** without typing to annotate using the project's labels.
4. As soon as ChatGPT returns valid annotations, they appear as ordinary editable
   annotations on the open image. Detection projects receive boxes, instance
   segmentation projects receive polygons, and classification projects receive
   image labels. Chat stays beside the canvas and contains a text summary.
5. Edit or delete unwanted annotations directly in the editor. **Undo** removes
   the most recently added batch; **Redo** restores it. Boxes and polygons are
   added to existing annotations; classification replaces the image's class
   labels. An empty result leaves existing annotations unchanged.
6. Select **Submit** to save through the normal dataset workflow. Clearing or
   closing chat keeps annotations that have already been added to the editor.

The current image is attached automatically to every annotation request. A paused
video frame can also be annotated from the editor. Changing the image or closing
the drawer cancels the pending request. The assistant validates label IDs and
coordinates before adding annotations; reviewing the result remains necessary
because model predictions can be inaccurate.

## Ask about a project or an uploaded image

Choose **Ask ChatGPT about this project** from the dataset's **Annotate** menu.
Use the attachment buttons to select a dataset image or images from your computer,
or paste an image into the message field. Supported file types are PNG, JPEG,
WebP, and GIF, up to 20 MB each and four attachments per message.

Project chat supports questions about datasets, models, and training. To apply
generated annotations to a dataset image, use **Annotate with ChatGPT** in the
image editor. Annotations added from this single-image flow are saved only after
**Submit**; Dataset Auto-Label saves its predictions as soon as the run completes.

## Connection status

The **Model** selector is visible directly below the chat header. Choose one of
the models returned by your ChatGPT account, or **Account default** to let Codex
choose. Geti remembers the selection for the next request and when you reopen the
app. Model selection is disabled while a response is running. If loading fails,
the selector remains visible with the error and **Retry model list**.

Geti reuses a confirmed ChatGPT account while the app is open and checks the
stored sign-in again after restarting. Opening another image or reopening the
drawer does not require signing in again. Account checks, model discovery, and
chat requests run through one queue so they cannot compete for the Codex process.

A failed connection check displays its error without clearing a previously
confirmed account. An actual signed-out response, successful **Sign out**, or a
change to the configured executable clears that account state.
