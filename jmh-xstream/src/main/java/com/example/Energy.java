package com.example;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.Arrays;

public class Energy {
    private final String root = "/sys/devices/virtual/powercap/intel-rapl/intel-rapl:";
    private final int cpuCount = 1;
    private long energies[];

    public Energy() {
        this.energies = new long[cpuCount];
    }

    public void init() throws IOException {
        for (int i = 0; i < cpuCount; i++) {
            this.energies[i] = Long.parseLong(new BufferedReader(new FileReader(root + i + "/energy_uj")).readLine());
        }
//        return;
    }

    public void stop() throws IOException {
        for (int i = 0; i < cpuCount; i++) {
            this.energies[i] = Long.parseLong(new BufferedReader(new FileReader(root + i + "/energy_uj")).readLine()) - this.energies[i];
        }
//        return;
    }

    public long getEnergy() {
        return Arrays.stream(this.energies).sum();
    }
}
