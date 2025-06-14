// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

//  Dependencies get bundled into the worker

import { expose } from 'comlink';
import localforage from 'localforage';

import { validateMediaSize } from '../pages/camera-page/media-validation-utils';
import { GETI_CAMERA_INDEXEDDB_INSTANCE_NAME, Screenshot } from '../pages/camera-support/camera.interface';
import { fetchMediaAndConvertToFile, getBlobFromDataUrl } from './utils';

declare const self: DedicatedWorkerGlobalScope;

const terminate = (): void => {
    self.close();
};

class Camera {
    storage: LocalForage;

    constructor(storeName: string) {
        this.storage = localforage.createInstance({ name: GETI_CAMERA_INDEXEDDB_INSTANCE_NAME, storeName });
    }

    /*
        Stores an item to the indexedDB
    */
    async setItem(id: string, screenshot: Screenshot) {
        if (!screenshot.dataUrl) {
            return Promise.reject('Error saving item, please refresh the page and try again.');
        }

        const blob = await getBlobFromDataUrl(screenshot.dataUrl);

        if (blob === undefined) {
            return;
        }

        const { message, error } = validateMediaSize(blob as File);

        if (error) {
            return Promise.reject(message);
        }

        return this.storage.setItem(id, { ...screenshot, file: blob });
    }

    /*
        Updates stored item on the indexedDB
        And initiates the upload process.

        To see how the upload process is initialized please refer to
        src/web_ui/src/pages/camera-page/components/loader-managers/dataset-loader-manager.component.tsx.

        But the gist is that we update the item with "isAccepted" key, which
        will then trigger the dataset loader useEffect and upload the files
    */
    async updateMedia(id: string, screenshot: Screenshot) {
        if (!screenshot.dataUrl) {
            return Promise.reject('Error saving item, please refresh the page and try again.');
        }

        const file = await fetchMediaAndConvertToFile(id, screenshot.dataUrl);

        if (!file) {
            return Promise.reject('Error uploading item, please refresh the page and try again.');
        }

        return this.storage.setItem(id, { ...screenshot, file });
    }

    /*
        Returns all items from indexedDB
    */
    async getItems() {
        const mediaItems: Screenshot[] = [];

        await this.storage.iterate((value: Omit<Screenshot, 'id'>, id) => {
            mediaItems.push({ id, ...value });
        });

        return mediaItems;
    }

    /*
        Returns an item from indexedDB
    */
    async getItem(id: string) {
        return this.storage.getItem<Screenshot>(id);
    }

    /*
        Deletes an item from indexedDB
    */
    async removeItem(id: string) {
        return this.storage.removeItem(id);
    }

    /*
        Deletes all items from indexedDB
    */
    async clear() {
        return this.storage.clear();
    }
}

const WorkerApi = { Camera, terminate };

expose(WorkerApi);
