// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { fetchClient } from '@/api';

import type { ToolDefinition } from '../types';

/** Upper bound on a single tool result, so one query cannot blow the prompt. */
const MAX_RESULT_CHARS = 12000;

/** Tail of a training log handed to the model, in lines. Failures are at the end. */
const MAX_LOG_LINES = 150;

/** Points kept per training curve; the raw series is far longer than useful. */
const MAX_METRIC_POINTS = 40;

const DEFAULT_CALIBRATION_SUBSET_SIZE = 100;

/**
 * Tools that change the installation. Each one is held for explicit user
 * approval before it runs — see `useAiChat`.
 */
export const ACTION_TOOLS: ReadonlySet<string> = new Set(['start_training', 'start_quantization', 'cancel_job']);

const noParameters = {
    type: 'object',
    properties: {},
    required: [],
    additionalProperties: false,
};

const projectParameter = (description: string) => ({
    type: 'object',
    properties: {
        project_id: {
            type: ['string', 'null'],
            description: `${description} Use null for the project the user currently has open.`,
        },
    },
    required: ['project_id'],
    additionalProperties: false,
});

const modelParameter = (description: string) => ({
    type: 'object',
    properties: {
        project_id: {
            type: ['string', 'null'],
            description: 'Id of the project. Use null for the project the user currently has open.',
        },
        model_id: {
            type: 'string',
            description,
        },
    },
    required: ['project_id', 'model_id'],
    additionalProperties: false,
});

/**
 * Most tools are read-only. The ones listed in {@link ACTION_TOOLS} change the
 * installation and only run once the user has approved them in the chat.
 */
export const GETI_TOOL_DEFINITIONS: ToolDefinition[] = [
    {
        type: 'function',
        name: 'list_projects',
        description: 'List every project in this Geti installation with its id, name and task type.',
        strict: true,
        parameters: noParameters,
    },
    {
        type: 'function',
        name: 'get_project',
        description:
            'Get one project: its task type, label definitions (name, colour, hotkey) and creation date. ' +
            'Call this before advising on labels, annotation guidelines or training.',
        strict: true,
        parameters: projectParameter('Id of the project to read.'),
    },
    {
        type: 'function',
        name: 'get_dataset_statistics',
        description:
            'Get dataset statistics for a project: media counts per type and the number of annotated media ' +
            'per label. Use this to judge dataset size, class balance and annotation progress.',
        strict: true,
        parameters: projectParameter('Id of the project whose dataset to inspect.'),
    },
    {
        type: 'function',
        name: 'list_media',
        description: 'List media items (images and videos) in a project dataset, newest first.',
        strict: true,
        parameters: {
            type: 'object',
            properties: {
                project_id: {
                    type: ['string', 'null'],
                    description: 'Id of the project. Use null for the project the user currently has open.',
                },
                limit: {
                    type: ['integer', 'null'],
                    description: 'How many items to return, at most 100. Defaults to 20.',
                },
            },
            required: ['project_id', 'limit'],
            additionalProperties: false,
        },
    },
    {
        type: 'function',
        name: 'list_models',
        description:
            'List the models trained in a project, with architecture, status, scores and creation date. ' +
            'Use this to compare runs or to explain why a model underperforms.',
        strict: true,
        parameters: projectParameter('Id of the project whose models to list.'),
    },
    {
        type: 'function',
        name: 'get_model',
        description:
            'Get one trained model in full: training status, device, start/end time, the labels it was trained ' +
            'on, and every variant (pytorch/openvino/onnx, fp32/fp16/int8) with its evaluation metrics per ' +
            'dataset subset. This is the first call when explaining a disappointing score.',
        strict: true,
        parameters: modelParameter('Id of the model to inspect.'),
    },
    {
        type: 'function',
        name: 'get_training_metrics',
        description:
            'Get the training curves of a model (loss, learning rate, validation metrics per epoch), downsampled. ' +
            'Use this to tell overfitting, underfitting, a diverging loss or a run that stopped too early apart.',
        strict: true,
        parameters: modelParameter('Id of the model whose training curves to read.'),
    },
    {
        type: 'function',
        name: 'get_training_logs',
        description:
            'Get the tail of the training log of a model. Use this when training failed or the metrics look ' +
            'broken, to find the actual error, warning or out-of-memory message.',
        strict: true,
        parameters: modelParameter('Id of the model whose log to read.'),
    },
    {
        type: 'function',
        name: 'list_dataset_revisions',
        description:
            'List the dataset revisions of a project with their train/validation/test item counts. Use this to ' +
            'check whether a model was trained on enough data and on a sane split.',
        strict: true,
        parameters: projectParameter('Id of the project whose dataset revisions to list.'),
    },
    {
        type: 'function',
        name: 'list_model_architectures',
        description:
            'List the model architectures Geti supports for a task, including the recommended picks for ' +
            'accuracy, balance and speed, plus benchmark metrics. Use this to recommend what to train.',
        strict: true,
        parameters: {
            type: 'object',
            properties: {
                task: {
                    type: 'string',
                    enum: ['classification', 'detection', 'instance_segmentation'],
                    description: 'Task type to list architectures for.',
                },
            },
            required: ['task'],
            additionalProperties: false,
        },
    },
    {
        type: 'function',
        name: 'list_training_devices',
        description:
            'List the devices available for training (CPU, Intel GPU/XPU, NVIDIA CUDA) with their memory. ' +
            'Use this before recommending a model size or batch size.',
        strict: true,
        parameters: noParameters,
    },
    {
        type: 'function',
        name: 'get_system_info',
        description: 'Get the Geti version, platform and license status of this installation.',
        strict: true,
        parameters: noParameters,
    },
    {
        type: 'function',
        name: 'list_jobs',
        description: 'List training, quantization, import and export jobs with their status and progress.',
        strict: true,
        parameters: noParameters,
    },
    {
        type: 'function',
        name: 'get_job',
        description:
            'Get one job by id: status, progress, and the error message when it failed. Use this to follow a ' +
            'job you started, or to explain why one failed.',
        strict: true,
        parameters: {
            type: 'object',
            properties: {
                job_id: { type: 'string', description: 'Id of the job to read.' },
            },
            required: ['job_id'],
            additionalProperties: false,
        },
    },
    {
        type: 'function',
        name: 'start_training',
        description:
            'Start a training job. The user is asked to confirm before this runs, so propose it freely, but call ' +
            'list_model_architectures and list_training_devices first and explain the choice. Returns the job, ' +
            'which you can follow with get_job.',
        strict: true,
        parameters: {
            type: 'object',
            properties: {
                project_id: {
                    type: ['string', 'null'],
                    description: 'Id of the project to train in. Use null for the project the user has open.',
                },
                model_architecture_id: {
                    type: 'string',
                    description: 'Architecture id exactly as returned by list_model_architectures.',
                },
                device: {
                    type: ['string', 'null'],
                    description:
                        'Device id such as "cpu", "xpu-0" or "cuda-0", built from list_training_devices as ' +
                        '"type" for CPU and "type-index" otherwise. Use null to take the first available device.',
                },
                parent_model_revision_id: {
                    type: ['string', 'null'],
                    description: 'Model revision to fine-tune from. Use null to start from pretrained weights.',
                },
                dataset_revision_id: {
                    type: ['string', 'null'],
                    description: 'Dataset revision to reuse. Use null to train on the latest dataset.',
                },
            },
            required: [
                'project_id',
                'model_architecture_id',
                'device',
                'parent_model_revision_id',
                'dataset_revision_id',
            ],
            additionalProperties: false,
        },
    },
    {
        type: 'function',
        name: 'start_quantization',
        description:
            'Start a quantization job that turns a trained model into a faster INT8 variant. The user is asked ' +
            'to confirm before this runs. Returns the job, which you can follow with get_job.',
        strict: true,
        parameters: {
            type: 'object',
            properties: {
                project_id: {
                    type: ['string', 'null'],
                    description: 'Id of the project. Use null for the project the user currently has open.',
                },
                model_id: {
                    type: 'string',
                    description: 'Id of the trained model revision to quantize, from list_models.',
                },
                max_calibration_subset_size: {
                    type: ['integer', 'null'],
                    description: `Calibration samples to use. Use null for the default of ${DEFAULT_CALIBRATION_SUBSET_SIZE}.`,
                },
                max_drop: {
                    type: ['number', 'null'],
                    description:
                        'Accuracy drop allowed, as a fraction between 0 and 1 (0.03 means 3%). ' +
                        'Use null to let Geti quantize without an accuracy constraint.',
                },
            },
            required: ['project_id', 'model_id', 'max_calibration_subset_size', 'max_drop'],
            additionalProperties: false,
        },
    },
    {
        type: 'function',
        name: 'cancel_job',
        description: 'Request cancellation of a running job. The user is asked to confirm before this runs.',
        strict: true,
        parameters: {
            type: 'object',
            properties: {
                job_id: { type: 'string', description: 'Id of the job to cancel.' },
            },
            required: ['job_id'],
            additionalProperties: false,
        },
    },
];

const stringify = (value: unknown): string => {
    const serialized = JSON.stringify(value ?? null);

    if (serialized.length <= MAX_RESULT_CHARS) {
        return serialized;
    }

    return `${serialized.slice(0, MAX_RESULT_CHARS)}… [truncated, ask for a narrower query]`;
};

const asRecord = (value: string): Record<string, unknown> => {
    try {
        const parsed: unknown = JSON.parse(value);

        return typeof parsed === 'object' && parsed !== null ? (parsed as Record<string, unknown>) : {};
    } catch {
        return {};
    }
};

const asString = (value: unknown, fallback: string): string =>
    typeof value === 'string' && value !== '' ? value : fallback;

const requireString = (value: unknown, field: string): string => {
    if (typeof value !== 'string' || value.trim() === '') {
        throw new Error(`The argument "${field}" is required.`);
    }

    return value;
};

const optionalString = (value: unknown): string | null => (typeof value === 'string' && value !== '' ? value : null);

/** Keeps the first, last and evenly spread points of a training curve. */
const downsample = <T>(points: T[], limit: number): T[] => {
    if (points.length <= limit) {
        return points;
    }

    const step = (points.length - 1) / (limit - 1);

    return Array.from({ length: limit }, (_, index) => points[Math.round(index * step)]);
};

/** A one-line, human description of an action, shown on the approval card. */
export const describeToolCall = (name: string, rawArguments: string): string => {
    const args = asRecord(rawArguments);

    switch (name) {
        case 'start_training':
            return `Train ${asString(args.model_architecture_id, 'a model')} on ${asString(args.device, 'the first available device')}.`;
        case 'start_quantization':
            return `Quantize model ${asString(args.model_id, '')} to INT8.`;
        case 'cancel_job':
            return `Cancel job ${asString(args.job_id, '')}.`;
        default:
            return name;
    }
};

type ToolExecutor = (args: Record<string, unknown>) => Promise<unknown>;

/**
 * Builds the executors for {@link GETI_TOOL_DEFINITIONS}. `currentProjectId` is
 * substituted whenever the model omits a project id, which is the common case.
 */
export const createGetiTools = (currentProjectId: string): Record<string, ToolExecutor> => {
    const projectOf = (args: Record<string, unknown>) => asString(args.project_id, currentProjectId);

    const unwrap = <T>(result: { data?: T; error?: unknown }): T => {
        if (result.error !== undefined) {
            throw new Error(stringify(result.error));
        }

        return result.data as T;
    };

    const trainingDevices = async () => unwrap(await fetchClient.GET('/api/system/devices/training'));

    // Mirrors the id the training dialog builds: "cpu", "xpu-0", "cuda-1".
    const resolveDevice = async (value: unknown): Promise<string> => {
        const requested = optionalString(value);

        if (requested !== null) {
            return requested;
        }

        const device = (await trainingDevices()).at(0);

        if (device === undefined) {
            throw new Error('No training device is available.');
        }

        return device.index == null ? device.type : `${device.type}-${device.index}`;
    };

    const modelPath = (args: Record<string, unknown>) => ({
        project_id: projectOf(args),
        model_id: requireString(args.model_id, 'model_id'),
    });

    return {
        list_projects: async () => unwrap(await fetchClient.GET('/api/projects')),

        get_project: async (args) =>
            unwrap(
                await fetchClient.GET('/api/projects/{project_id}', {
                    params: { path: { project_id: projectOf(args) } },
                })
            ),

        get_dataset_statistics: async (args) =>
            unwrap(
                await fetchClient.GET('/api/projects/{project_id}/dataset/statistics', {
                    params: { path: { project_id: projectOf(args) }, query: { dataset_view_id: null } },
                })
            ),

        list_media: async (args) => {
            const limit = typeof args.limit === 'number' ? Math.min(Math.max(args.limit, 1), 100) : 20;

            return unwrap(
                await fetchClient.GET('/api/projects/{project_id}/dataset/media', {
                    params: { path: { project_id: projectOf(args) }, query: { limit } },
                })
            );
        },

        list_models: async (args) =>
            unwrap(
                await fetchClient.GET('/api/projects/{project_id}/models', {
                    params: { path: { project_id: projectOf(args) } },
                })
            ),

        get_model: async (args) =>
            unwrap(
                await fetchClient.GET('/api/projects/{project_id}/models/{model_id}', {
                    params: { path: modelPath(args) },
                })
            ),

        get_training_metrics: async (args) => {
            const { training_metrics } = unwrap(
                await fetchClient.GET('/api/projects/{project_id}/models/{model_id}/training_metrics', {
                    params: { path: modelPath(args) },
                })
            );

            return training_metrics.map((metric) => ({
                name: metric.header,
                x_axis: metric.value.x_axis_label,
                y_axis: metric.value.y_axis_label,
                series: metric.value.line_data.map((line) => ({
                    name: line.header,
                    points: downsample(line.points, MAX_METRIC_POINTS).map(({ x, y }) => [x, y]),
                })),
            }));
        },

        get_training_logs: async (args) => {
            const text = unwrap(
                await fetchClient.GET('/api/projects/{project_id}/models/{model_id}/logs', {
                    params: { path: modelPath(args) },
                    parseAs: 'text',
                })
            );

            const lines = (text ?? '').split('\n').filter((line) => line.trim() !== '');

            return { total_lines: lines.length, tail: lines.slice(-MAX_LOG_LINES) };
        },

        list_dataset_revisions: async (args) =>
            unwrap(
                await fetchClient.GET('/api/projects/{project_id}/dataset_revisions', {
                    params: { path: { project_id: projectOf(args) } },
                })
            ),

        list_model_architectures: async (args) => {
            const task = args.task;

            if (task !== 'classification' && task !== 'detection' && task !== 'instance_segmentation') {
                throw new Error('Unknown task type.');
            }

            return unwrap(await fetchClient.GET('/api/model_architectures', { params: { query: { task } } }));
        },

        list_training_devices: async () => trainingDevices(),

        get_system_info: async () => unwrap(await fetchClient.GET('/api/system/info')),

        list_jobs: async () => unwrap(await fetchClient.GET('/api/jobs')),

        get_job: async (args) =>
            unwrap(
                await fetchClient.GET('/api/jobs/{job_id}', {
                    params: { path: { job_id: requireString(args.job_id, 'job_id') } },
                })
            ),

        start_training: async (args) =>
            unwrap(
                await fetchClient.POST('/api/jobs', {
                    body: {
                        job_type: 'train',
                        project_id: projectOf(args),
                        parameters: {
                            device: await resolveDevice(args.device),
                            model_architecture_id: requireString(args.model_architecture_id, 'model_architecture_id'),
                            parent_model_revision_id: optionalString(args.parent_model_revision_id),
                            dataset_revision_id: optionalString(args.dataset_revision_id),
                        },
                    },
                })
            ),

        start_quantization: async (args) =>
            unwrap(
                await fetchClient.POST('/api/jobs', {
                    body: {
                        job_type: 'quantize',
                        project_id: projectOf(args),
                        parameters: {
                            model_id: requireString(args.model_id, 'model_id'),
                            max_calibration_subset_size:
                                typeof args.max_calibration_subset_size === 'number'
                                    ? args.max_calibration_subset_size
                                    : DEFAULT_CALIBRATION_SUBSET_SIZE,
                            max_drop: typeof args.max_drop === 'number' ? args.max_drop : null,
                        },
                    },
                })
            ),

        cancel_job: async (args) =>
            unwrap(
                await fetchClient.POST('/api/jobs/{job_id}:cancel', {
                    params: { path: { job_id: requireString(args.job_id, 'job_id') } },
                })
            ),
    };
};

/**
 * Runs one model-requested tool call and returns the JSON string that goes back
 * into the transcript. Failures are reported to the model rather than thrown, so
 * it can explain the problem or try a different tool.
 */
export const executeToolCall = async (
    tools: Record<string, ToolExecutor>,
    name: string,
    rawArguments: string
): Promise<{ output: string; failed: boolean }> => {
    const tool = tools[name];

    if (tool === undefined) {
        return { output: stringify({ error: `Unknown tool "${name}".` }), failed: true };
    }

    try {
        return { output: stringify(await tool(asRecord(rawArguments))), failed: false };
    } catch (error: unknown) {
        const message = error instanceof Error ? error.message : 'The tool call failed.';

        return { output: stringify({ error: message }), failed: true };
    }
};
