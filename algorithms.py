import collections
from multiprocessing import Process, shared_memory
from multiprocessing.shared_memory import SharedMemory

import numpy
import numpy as np

import main

SAMPLE_FREQUENCY = 512

def start_algorithm(data: numpy.ndarray, samplerate: int, shared_buf_result: SharedMemory, algorithm_id: int, thread_count: int):
    # data is expected to have a shape of (n, 2), where n is the number of sample pairs
    # and a samplerate of 48000. Results might still work for other sample rates, but could be less
    # accurate.
    # TODO rewrite so that shared_memory buffer is passed as argument, and computation can be done
    #  in a streaming manner (assuming processing speed is faster than playing speed, which should be the case with
    #  modern CPUs).

    algorithms = [algo_uno, algo_dos]

    if algorithm_id > len(algorithms):
        print(f"Algorithm {algorithm_id} does not exist!")
        exit(2)

    print("Spawning threads...")
    for i in range(thread_count):
        result = shared_memory.SharedMemory(shared_buf_result.name)
        Process(target=algorithms[algorithm_id-1], args=(data, samplerate, result, i, thread_count)).start()
        print(f"Spawned thread {i}")
    print("Threads spawned")


def algo_uno(data: numpy.ndarray, samplerate: int, result: SharedMemory, thread_id, thread_count):
    # data is expected to have a shape of (n, 2), where n is the number of sample pairs
    # and a samplerate of 48000. Results might still work for other sample rates, but could be less
    # accurate.
    # TODO dynamically generate sample # for average energy (1s) and instant (20ms)

    # Calculate initial average energy (prefill buffer with first 48128 samples)
    avg_e = 0
    variance = 0
    SENSIBILITY_CONST = 1.7
    for a, b in data[:48128]:
        avg_e += a * a + b * b
    avg_e *= SAMPLE_FREQUENCY / 48128

    for i in range(thread_id*SAMPLE_FREQUENCY, data.shape[0], SAMPLE_FREQUENCY*thread_count):
        if (i//SAMPLE_FREQUENCY) % (thread_count*10) == 0:
            print(f"[{thread_id}] {i} ({100*float(i)/data.shape[0]:.2f}%)")
        # 48128 samples ~= 1s
        if i > 48128:
            # New instant energy slice after initial buffer depleted, "shift" buffer and add last 1024
            avg_e = 0
            for a, b in data[i-48128:i]:
                avg_e += (a * a + b * b)
            avg_e *= SAMPLE_FREQUENCY / 48128

            # compute variance of energies (V)


        # Compute instant energy (inst_e)
        inst_e = 0
        for a, b in data[i:i+SAMPLE_FREQUENCY]:
            inst_e += a * a + b * b

        result.buf[i//SAMPLE_FREQUENCY] = 1 if inst_e >= SENSIBILITY_CONST * avg_e else 0

    return result

def algo_dos(data: numpy.ndarray, samplerate: int, result: SharedMemory, thread_id, thread_count):
    # data is expected to have a shape of (n, 2), where n is the number of sample pairs
    # and a samplerate of 48000. Results might still work for other sample rates, but could be less
    # accurate.
    w1 = 5
    SENSIBILITY_CONST = 1.5
    n = 64
    e_i = []
    c_buf = [0] * SAMPLE_FREQUENCY
    fe = 48128
    v0 = 150
    f_max = 48128

    for i in range(n):
        e_i.append(collections.deque([], maxlen=48))

    for i in range(thread_id * SAMPLE_FREQUENCY, data.shape[0], SAMPLE_FREQUENCY * thread_count):
        e_s = np.zeros(n)
        c = np.empty(SAMPLE_FREQUENCY, dtype="complex128")

        # (a_n)+i*(b_n)
        for j, (a, b) in enumerate(data[i:i+SAMPLE_FREQUENCY]):
            c[j] = a + 1j * b

        # FFT goes from (a_n)+i*(b_n) --> buffer (B) with 1024 frequency amplitudes
        c_fft = np.fft.fft(c)
        for j in range(len(c_fft)):
            imag = np.imag(c_fft[j])
            real = np.real(c_fft[j])
            c_buf[j] = imag * imag + real * real

        # # R7, calculating each subbands energy (Es)
        # for j in range(e_s.shape[0]):
        #     e_s[j] += np.sum(c_buf[j:j+n])
        # e_s *= 32 / SAMPLE_FREQUENCY

        # R7' , calculating each subbands energy logarithmically
        a = ((2 * SAMPLE_FREQUENCY) - 2 * n * w1)/(n * n - n)
        b = w1 - a
        prev_w = 0
        for j in range(e_s.shape[0]):
            # R10
            if j == e_s.shape[0]:
                w = SAMPLE_FREQUENCY - prev_w
            else:
                w = int(np.ceil(a * j + b))

            e_s[j] += np.sum(c_buf[prev_w:prev_w+w])
            e_s[j] *= w / SAMPLE_FREQUENCY

            prev_w += w

        # R13 and R14
        # added 32 to denominator to account for subband division
        upper_idx = SAMPLE_FREQUENCY - (f_max * SAMPLE_FREQUENCY) / (fe * 32)
        lower_idx = (f_max * SAMPLE_FREQUENCY) / (fe * 32)

        for j in range(n):

            #isolate subbands in frequency range: 0 - f_max
            if j >= lower_idx and j <= upper_idx:

                #initial condition
                if len(e_i[j]) == 0:
                    e_i_avg = 9e99
                    e_i_var = 9e99
                else:

                    # R8, finding Ei average
                    e_i_avg = sum(e_i[j])/len(e_i[j])

                    # R15, find variance
                    e_i_var = 0
                    for e_i_k in e_i[j]:
                        e_i_var += (e_i_k - e_i_avg) * (e_i_k - e_i_avg)
                    e_i_var /= 43

                #check for beat
                if (e_s[j] >= SENSIBILITY_CONST * e_i_avg) and (e_i_var > v0):
                    result.buf[i // 1024] = 1
                e_i[j].append(e_s[j])
