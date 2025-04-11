// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { delay } from '../utils';
import { ConcurrentItemProcessor, QueuedItem } from './concurrent-item-processor';

function limitConcurrentProcesses<T>(maxNumberOfConcurrentProcesses: number) {
    return async (items: Array<T>, toBeProcessed: Array<T>): Promise<Array<T>> => {
        const amount = Math.max(maxNumberOfConcurrentProcesses - items.length, 0);

        return toBeProcessed.slice(0, amount);
    };
}

describe('Concurrent item processor', () => {
    it('runs two processes concurrently', async () => {
        const sequence: number[] = [];

        const process = async ([idx, time]: [number, number]) => {
            if (time > 0) {
                await delay(time);
            }

            sequence.push(idx);
        };

        const queue = new ConcurrentItemProcessor(process, limitConcurrentProcesses(2));

        const wait = 10;
        await Promise.all([
            queue.addItem([0, 0]),
            queue.addItem([1, wait]),
            queue.addItem([2, 0]),
            queue.addItem([3, wait]),
            queue.addItem([4, 0]),
            queue.addItem([5, wait]),
            queue.addItem([6, 0]),
            queue.addItem([7, wait]),
            queue.addItem([8, 0]),
        ]);

        expect(sequence).toEqual([
            0, // 0
            2, // 0
            1, // wait
            4, // 0
            3, // wait
            6, // 0
            5, // wait
            8,
            7,
        ]);
    });

    it('runs three processes concurrently', async () => {
        const sequence: number[] = [];

        const process = async ([idx, time]: [number, number]) => {
            if (time > 0) {
                await delay(time);
            }

            sequence.push(idx);
        };

        const queue = new ConcurrentItemProcessor(process, limitConcurrentProcesses(3));

        const wait = 10;
        await Promise.all([
            queue.addItem([0, 0]),
            queue.addItem([1, wait]),
            queue.addItem([2, 0]),
            queue.addItem([3, wait]),
            queue.addItem([4, 0]),
            queue.addItem([5, wait]),
            queue.addItem([6, 0]),
            queue.addItem([7, wait]),
            queue.addItem([8, 0]),
        ]);

        expect(sequence).toEqual([
            0, // 0
            2, // 0
            4, // 0
            1, // wait
            6, // 0
            3, // wait
            8,
            5, // wait
            7,
        ]);
    });

    it('runs in sequance', async () => {
        const sequence: number[] = [];

        const process = async ([idx, time]: [number, number]) => {
            if (time > 0) {
                await delay(time);
            }

            sequence.push(idx);
        };

        const queue = new ConcurrentItemProcessor(process, limitConcurrentProcesses(4));

        const wait = 10;
        await Promise.all([
            queue.addItem([0, 0]),
            queue.addItem([1, wait]),
            queue.addItem([2, 0]),
            queue.addItem([3, wait]),
            queue.addItem([4, 0]),
            queue.addItem([5, wait]),
            queue.addItem([6, 0]),
            queue.addItem([7, wait]),
            queue.addItem([8, 0]),
        ]);

        expect(sequence).toEqual([0, 2, 4, 6, 1, 8, 3, 5, 7]);
    });

    it('does not execute any items', async () => {
        const process = async (idx: number) => {
            return idx;
        };

        const queue = new ConcurrentItemProcessor(process, async () => {
            return [];
        });

        let resolved = false;
        const promise = Promise.any([queue.addItem(0), queue.addItem(1)]).then(() => {
            resolved = true;
        });

        // Either wait for a timeout or until the process have finished
        await Promise.any([delay(20), promise]);

        expect(resolved).toBe(false);
    });

    it('cancels processing items when the queue is cleared', async () => {
        const sequence: number[] = [];

        const process = async (idx: number) => {
            await delay(50);

            sequence.push(idx);
            return idx;
        };

        const queue = new ConcurrentItemProcessor(process, limitConcurrentProcesses(2));

        const promises = Promise.all([
            queue.addItem(0),
            queue.addItem(1),
            queue.addItem(2),
            queue.addItem(3),
            queue.addItem(4),
            queue.addItem(5),
        ]);

        queue.clear();

        try {
            await promises;
        } catch (error) {
            expect(error).toEqual('Cancelled');
        }

        expect(sequence).toEqual([]);
    });

    it('can make an item skip to the end of the queuee', async () => {
        const sequence: number[] = [];

        const process = async ({ idx }: { idx: number; type: 'image' | 'video' }) => {
            sequence.push(idx);
            return idx;
        };

        const limit = limitConcurrentProcesses<QueuedItem<{ idx: number; type: 'image' | 'video' }>>(2);

        const queue = new ConcurrentItemProcessor(process, async (items, nextItems) => {
            const nextItemsWithinConcurrencyLimit = await limit(items, nextItems);

            return items.length > 0 || nextItemsWithinConcurrencyLimit.length > 1
                ? nextItemsWithinConcurrencyLimit.filter((x) => x.item.type !== 'video')
                : nextItemsWithinConcurrencyLimit;
        });

        await Promise.all([
            queue.addItem({ idx: 0, type: 'image' }),
            queue.addItem({ idx: 1, type: 'image' }),
            queue.addItem({ idx: 2, type: 'image' }),
            queue.addItem({ idx: 3, type: 'video' }),
            queue.addItem({ idx: 4, type: 'image' }),
            queue.addItem({ idx: 5, type: 'image' }),
        ]);

        expect(sequence).toEqual([0, 1, 2, 4, 5, 3]);
    });

    it('can handle complex concurrency rules', async () => {
        const sequence: number[] = [];
        const currentlyProcessing: number[] = [];

        const process = async ({ idx, type }: { idx: number; type: 'image' | 'video' }) => {
            currentlyProcessing.push(idx);

            if (type === 'video') {
                await delay(50);
            } else {
                await delay(30);
            }

            sequence.push(idx);
            return idx;
        };

        type Item = QueuedItem<{ idx: number; type: 'image' | 'video' }>;
        const limit = limitConcurrentProcesses<Item>(6);

        const concurrencyRule = async (items: Array<Item>, nextItems: Array<Item>): Promise<Array<Item>> => {
            const nextItemsWithinConcurrencyLimit = await limit(items, nextItems);

            const nextItem = nextItemsWithinConcurrencyLimit.at(0);

            if (nextItem?.item.type === 'video') {
                return items.length > 0 ? [] : [nextItem];
            }

            if (nextItem !== undefined && nextItemsWithinConcurrencyLimit.some(({ item }) => item.type === 'video')) {
                const videoIdx = nextItemsWithinConcurrencyLimit.findIndex(({ item }) => item.type === 'video');

                return nextItemsWithinConcurrencyLimit.slice(0, videoIdx);
            }

            return nextItemsWithinConcurrencyLimit;
        };
        const queue = new ConcurrentItemProcessor(process, concurrencyRule);

        const finishProcessing = async (x: number | null) => {
            const idx = currentlyProcessing.findIndex((y) => y === x);
            currentlyProcessing.splice(idx);
            return x;
        };
        await Promise.all([
            queue.addItem({ idx: 0, type: 'image' }).then(finishProcessing),
            queue.addItem({ idx: 1, type: 'image' }).then(finishProcessing),
            queue.addItem({ idx: 2, type: 'image' }).then(finishProcessing),
            queue.addItem({ idx: 3, type: 'video' }).then(finishProcessing),
            queue.addItem({ idx: 4, type: 'image' }).then(finishProcessing),
            queue.addItem({ idx: 5, type: 'image' }).then(finishProcessing),
            queue.addItem({ idx: 6, type: 'image' }).then(finishProcessing),
            queue.addItem({ idx: 7, type: 'image' }).then(finishProcessing),
            queue.addItem({ idx: 8, type: 'image' }).then(finishProcessing),
            queue.addItem({ idx: 9, type: 'image' }).then(finishProcessing),
        ]);

        expect(sequence).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
    });

    it('tracks errors when processing an item', async () => {
        const errors: Error[] = [];
        const successes: number[] = [];

        const process = async ([idx, error]: [number, Error] | [number]) => {
            if (error) {
                throw error;
            }

            return idx;
        };

        const queue = new ConcurrentItemProcessor(process, limitConcurrentProcesses(1));

        const errrorToThrow = new Error('error');
        const handlePromise = async (promise: Promise<number | null>) => {
            try {
                const result = await promise;
                if (result !== null) {
                    successes.push(result);
                }
                return result;
            } catch (e) {
                errors.push(e as Error);
            }
        };

        await Promise.all([
            handlePromise(queue.addItem([0])),
            handlePromise(queue.addItem([1, errrorToThrow])),
            handlePromise(queue.addItem([2])),
        ]);

        expect(successes).toEqual([0, 2]);
        expect(errors).toEqual([errrorToThrow]);
    });

    it('can run 3 processes concurrently', async () => {
        const sequence: number[] = [];

        const process = async ([idx, time]: [number, number]) => {
            if (time > 0) {
                await delay(time);
            }

            sequence.push(idx);
        };

        const queue = new ConcurrentItemProcessor(process, limitConcurrentProcesses(3));

        await Promise.all([
            queue.addItem([0, 200]),
            queue.addItem([1, 100]),
            queue.addItem([2, 50]),
            queue.addItem([3, 100]),
            queue.addItem([4, 100]),
            queue.addItem([5, 100]),
            queue.addItem([6, 100]),
            queue.addItem([7, 100]),
            queue.addItem([8, 100]),
        ]);

        expect(sequence).toEqual([0, 2, 1, 3, 4, 5, 6, 7, 8]);
    });

    it('runs many processes concurrently', async () => {
        const sequence: number[] = [];

        const process = async (idx: number) => {
            await delay(10);

            sequence.push(idx);
        };

        // Allow for all processes to be run at the same time
        const queue = new ConcurrentItemProcessor(process, limitConcurrentProcesses(10));

        await Promise.all([
            queue.addItem(0),
            queue.addItem(1),
            queue.addItem(2),
            queue.addItem(3),
            queue.addItem(4),
            queue.addItem(5),
            queue.addItem(6),
            queue.addItem(7),
            queue.addItem(8),
            queue.addItem(9),
        ]);

        expect(sequence).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
    });
});
