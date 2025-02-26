package com.example;

import com.thoughtworks.xstream.XStream;
import com.thoughtworks.xstream.io.xml.StaxDriver;
import com.thoughtworks.xstream.security.AnyTypePermission;
import org.openjdk.jmh.annotations.*;
import org.openjdk.jmh.infra.Blackhole;
import org.openjdk.jmh.results.format.ResultFormatType;
import org.openjdk.jmh.runner.Runner;
import org.openjdk.jmh.runner.options.Options;
import org.openjdk.jmh.runner.options.OptionsBuilder;

import java.io.*;
import java.lang.management.ManagementFactory;
import java.util.concurrent.TimeUnit;

public class App {
    @Benchmark
    @Warmup(iterations = 2, time = 3)
    @Measurement(iterations = 2, time = 5)
    //@BenchmarkMode(Mode.AverageTime)
    @BenchmarkMode({Mode.All})
    @OutputTimeUnit(TimeUnit.SECONDS)
    public Void benchmarkSerializationWithGSON(Blackhole bh) {
        try {
            Energy j = new Energy();
            j.init();
            XStream xstream = new XStream(new StaxDriver());
            xstream.addPermission(AnyTypePermission.ANY);
            xstream.alias("row", AUser.class);
            xstream.alias("friend", Friend.class);
            xstream.alias("root", AUser[].class);
            xstream.addImplicitCollection(AUser.class, "tags", String.class);
            xstream.addImplicitCollection(AUser.class, "friends", Friend.class);
            File xmlFile = new File("/home/waheed/.local/share/JetBrains/users5000-10.xml");
            AUser[] users = (AUser[]) xstream.fromXML(new FileInputStream(xmlFile));
            Writer writer = new FileWriter(new File("/home/waheed/.local/share/JetBrains/marshalled"));
            writer.write(xstream.toXML(users));
            writer.close();
            j.stop();
            System.out.print(j.getEnergy() + "+ ");
        } catch (IOException e) {
            e.printStackTrace();
        }
        return null;
    }
    public static void main(String... args) throws Exception {
        Options opts = new OptionsBuilder()
                .include(App.class.getSimpleName())
//                .resultFormat(ResultFormatType.CSV)
//                .result("../assigned_tasks/Final-Results/XSTREAM-Results/result.csv")
                .forks(1)
                .build();
        new Runner(opts).run();
    }
}
