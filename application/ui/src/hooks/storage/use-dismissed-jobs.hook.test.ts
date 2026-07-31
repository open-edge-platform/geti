// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { act, renderHook } from '@testing-library/react';

import { DISMISSED_JOBS_KEY, useDismissedJobs } from './use-dismissed-jobs.hook';

describe('useDismissedJobs', () => {
    afterEach(() => {
        sessionStorage.clear();
    });

    it('does not report a job as dismissed by default', () => {
        const { result } = renderHook(() => useDismissedJobs());

        expect(result.current.isJobDismissed('job-1')).toBe(false);
    });

    it('reports a job as dismissed once it has been dismissed', () => {
        const { result } = renderHook(() => useDismissedJobs());

        act(() => {
            result.current.dismissJob('job-1');
        });

        expect(result.current.isJobDismissed('job-1')).toBe(true);
        expect(result.current.isJobDismissed('job-2')).toBe(false);
    });

    it('does not store the same job twice', () => {
        const { result } = renderHook(() => useDismissedJobs());

        act(() => {
            result.current.dismissJob('job-1');
        });
        act(() => {
            result.current.dismissJob('job-1');
        });

        expect(JSON.parse(sessionStorage.getItem(DISMISSED_JOBS_KEY) ?? '[]')).toEqual(['job-1']);
    });

    it('shares dismissed jobs between hook instances', () => {
        const { result: firstInstance } = renderHook(() => useDismissedJobs());
        const { result: secondInstance } = renderHook(() => useDismissedJobs());

        act(() => {
            firstInstance.current.dismissJob('job-1');
        });

        expect(secondInstance.current.isJobDismissed('job-1')).toBe(true);
    });

    it('reads jobs that were already dismissed in the session', () => {
        sessionStorage.setItem(DISMISSED_JOBS_KEY, JSON.stringify(['job-1']));

        const { result } = renderHook(() => useDismissedJobs());

        expect(result.current.isJobDismissed('job-1')).toBe(true);
    });
});
