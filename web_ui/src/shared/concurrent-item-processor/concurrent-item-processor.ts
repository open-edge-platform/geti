// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { v4 as uuid } from 'uuid';

interface FinishedProcessResult<Result> {
    isSuccess: boolean;
    result: Result | null;
    error: unknown;
}
export interface QueuedItem<Item> {
    id: string;
    item: Item;
}

export class ConcurrentItemProcessor<Item, Result> {
    private itemQueue: Array<QueuedItem<Item>>;
    private itemsBeingProcessed: { [id: string]: QueuedItem<Item> };
    private callbacks: {
        [id: string]: (result: FinishedProcessResult<Result>) => void;
    };
    private isProcessing = false;

    constructor(
        private process: (item: Item) => Promise<Result>,
        private getNextItemsToProcess: (
            items: QueuedItem<Item>[],
            nextItems: QueuedItem<Item>[]
        ) => Promise<Array<QueuedItem<Item>>>
    ) {
        this.itemQueue = [];
        this.itemsBeingProcessed = {};
        this.callbacks = {};
    }

    public numberOfQueuedItems(): number {
        return this.itemQueue.length;
    }

    public numberOfExecutingItems(): number {
        return Object.keys(this.itemsBeingProcessed).length;
    }

    /**
     * Adds an item to the internal queue of items to be procesed and returns a
     * promise that once processed will be called with its result
     **/
    public addItem(item: Item): Promise<Result | null> {
        return new Promise(async (resolve, reject) => {
            const id = uuid();

            // Keep track of the items to be processed and either resolve
            // or reject the current promise based on the process result
            this.itemQueue.push({ id, item });
            this.callbacks[id] = (result) => {
                if (result.isSuccess) {
                    resolve(result.result);
                } else {
                    reject(result.error);
                }
            };

            // Trigger the process queue to start if it hasn't started already
            this.execute();
        });
    }

    /**
     * Empty the process queue and reject any of the referenced promises
     **/
    public clear(): void {
        // Empty current queue
        for (const { id } of this.itemQueue) {
            this.cancelItem(id);
        }
        this.itemQueue = [];

        // Make all promises error
        for (const id of Object.keys(this.itemsBeingProcessed)) {
            this.cancelItem(id);
        }
    }

    /**
     * Start processing all items in the process queue
     **/
    public async execute(): Promise<void> {
        if (this.isProcessing || this.itemQueue.length === 0) {
            return;
        }

        // Make sure that we process the queue one process at a time,
        // this is required because the concurrencyRule is async,
        // which could otherwise result in items being processedt twice
        this.isProcessing = true;

        const itemsToProcess = await this.getNextItemsToProcess(
            Object.values(this.itemsBeingProcessed),
            this.itemQueue
        );

        this.itemQueue = this.itemQueue.filter((item) => {
            return !itemsToProcess.some(({ id }) => id === item.id);
        });

        for (const nextItemToProcess of itemsToProcess) {
            const id = nextItemToProcess.id;
            const callback = this.callbacks[id];

            if (!callback) {
                continue;
            }
            this.itemsBeingProcessed[id] = nextItemToProcess;

            // run the promise and pass the result back to the callback associated with this promise
            this.process(nextItemToProcess.item)
                .then((res) => {
                    delete this.callbacks[id];
                    delete this.itemsBeingProcessed[id];

                    callback({ isSuccess: true, result: res, error: null });
                })
                .catch((err) => {
                    delete this.callbacks[id];
                    delete this.itemsBeingProcessed[id];

                    callback({ isSuccess: false, result: null, error: err });
                })
                .finally(() => {
                    this.execute();
                });
        }

        this.isProcessing = false;
    }

    private cancelItem(id: string) {
        const callback = this.callbacks[id];

        callback({ error: 'Cancelled', isSuccess: false, result: null });

        delete this.callbacks[id];
        delete this.itemsBeingProcessed[id];
    }
}
